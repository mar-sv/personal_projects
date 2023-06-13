import mikeio as mi
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gdp
from shapely.geometry import Point, LineString
import sys
from math import atan2, degrees, hypot, radians, cos, sin
import shapely.wkt
import shapely.ops


def reverse_geom(geom):
    def _reverse(x, y, z=None):
        if z:
            return x[::-1], y[::-1], z[::-1]
        return x[::-1], y[::-1]

    return shapely.ops.transform(_reverse, geom)


def get_grid_size(ds):
    # Check if quadratic grid
    if ds.geometry.dx != ds.geometry.dy:
        print('The grid is not quadratic. This might cause insufficient results')
    return ds.geometry.dx


def PerpendicularFor2Points(pointA, pointB):
    changeInX = pointB[0] - pointA[0]
    changeInY = pointB[1] - pointA[1]
    return atan2(changeInY, changeInX)+radians(90)


def calculate_flow_magnitude(df1, df2, grid_size, perpendicular_line):

    # Create resultant df of the two
    resultant_df = pd.DataFrame(columns=['time', 'Discharge + [meter^3/s]', 'Discharge - [meter^3/s]',
                                'Discharge [meter^3/s]', 'Cum. disc. + [meter^3]', 'Cum. disc. - [meter^3]', 'Cum. disc. [meter^3/s]'])
    resultant_df['time'] = df1.index
    # Get columns of input dfs (easier access)
    inc_columns = df1.columns
    print(perpendicular_line)
    # Resultant flow is given by hypothenuse of both. Note that the flow is given in per meter, meaning that we need to multiply by the grid size
    df1['Discharge [meter^3/s]'] = df1.apply(
        lambda x: (x[inc_columns[2]]*sin(perpendicular_line) + x[inc_columns[1]]*cos(perpendicular_line)), axis=1)
    df2['Discharge [meter^3/s]'] = df2.apply(
        lambda x: (x[inc_columns[2]]*sin(perpendicular_line) + x[inc_columns[1]]*cos(perpendicular_line)), axis=1)

    resultant_df['Discharge [meter^3/s]'] = (df1['Discharge [meter^3/s]'] + df2['Discharge [meter^3/s]'])/2 * grid_size
    res_columns = resultant_df.columns
    # Update the columns, and calculate flow direction
    resultant_df['Discharge + [meter^3/s]'] = resultant_df.apply(
        lambda x: x[res_columns[4]] if x[res_columns[4]] > 0 else 0, axis=1)
    resultant_df['Discharge - [meter^3/s]'] = resultant_df.apply(
        lambda x: x[res_columns[4]] if x[res_columns[4]] < 0 else 0, axis=1)

    # Calculate the cumulative sum of the flows
    resultant_df['Cum. disc. + [meter^3]'] = np.cumsum(
        resultant_df['Discharge + [meter^3/s]'])
    resultant_df['Cum. disc. - [meter^3]'] = np.cumsum(
        resultant_df['Discharge - [meter^3/s]'])
    # resultant_df['Cum. disc. [meter^3/s]'] = np.cumsum(resultant_df['Discharge [meter^3/s]'])
    return resultant_df


def get_values_for_linestring(grid_size, ds, geometry_row):
    result_df = pd.DataFrame(columns=['time', 'Discharge + [meter^3/s]', 'Discharge - [meter^3/s]',
                             'Discharge [meter^3/s]', 'Cum. disc. + [meter^3]', 'Cum. disc. - [meter^3]', 'Cum. disc. [meter^3/s]'])
    # Number of points in the polyline
    num_coords = len(geometry_row.coords)

    # Convert gridsize to integer
    grid_size = int(grid_size)

    # We will take timesteps equal to grid_size/2 in order not to miss any of the cells.
    # However, in order to not duplicate any of the cells, we need to check whether the coordinates have been calculated before
    calculated_coords = []

    # Loop through each coordinate, create a new polyline for each and extract result
    for j in range(1, num_coords):

        # Define start and end coordinates
        starting_coord = geometry_row.coords[j-1]
        end_coord = geometry_row.coords[j]
        # Create new LineString of new coordinates and calculate its perpendicular angle
        sub_line = LineString([starting_coord, end_coord])
        perpendicular_angle = PerpendicularFor2Points(
            starting_coord, end_coord)

        # Round the length of the line to closest integer and convert
        length_of_line = int(
            np.round(Point(starting_coord).distance(Point(end_coord)), 0))

        # Loop thorugh the values in the dfs2 file, with the step size equivalent to the gridsize
        for i in range(0, length_of_line, grid_size):

            # Get first coord of subline
            ip1 = sub_line.interpolate(distance=i)
            point_array = ds.sel(x=ip1.coords[0][0], y=ip1.coords[0][1])
            df1 = point_array.to_dataframe()

            # Get second coord of subline
            ip2 = sub_line.interpolate(distance=i+grid_size)
            point_array = ds.sel(x=ip2.coords[0][0], y=ip2.coords[0][1])
            df2 = point_array.to_dataframe()
            # Get coordinates of point with i distance from start coordinate

            temp_df = calculate_flow_magnitude(
                df1, df2, grid_size, perpendicular_angle)
            result_df = pd.concat([temp_df, result_df])
            # REMEMBER! NOW THE IDEA IS TO TAKE THE PREV_DF AND CURR_DF AND CALCULATE THE AVERAGE!!!!!
            # Check whether the point have been calculated before
        #    new_coord_list = [point_array.geometry.x, point_array.geometry.y]
        #    if new_coord_list not in calculated_coords:
            # Create a df with this cross sections values
        #        df_next_coord = point_array.to_dataframe()

            # Calculate flow magnitude and its direction
        #        df_next_coord = calculate_flow_magnitude(
        #            df_next_coord, grid_size, perpendicular_angle)
            # Concatenate the results of the new coordinate to result_df. Note that here they are concatenated vertically
        #        df_result = pd.concat([df_result, df_next_coord])

            # append the coordinates to calculated_coords
        #        calculated_coords.append(new_coord_list)

    # TEST! Include last coord.
    # Extract results
    # point_array = ds.sel(x=end_coord[0], y=end_coord[1])
    # new_coord_list = [point_array.geometry.x, point_array.geometry.y]

    # if new_coord_list not in calculated_coords:
        # Extract results for each item in the dfs2
        # print("Du missade sista!!!")
    #    df_next = point_array.to_dataframe()
    #    df_next_coord = calculate_flow_magnitude(
    #        df_next, grid_size, perpendicular_angle)
        # Add the coordinates of point_array to our memory list
    #    df_result = pd.concat([df_result, df_next_coord])
    #    calculated_coords.append(new_coord_list)

    # result_df = result_df.groupby('time', as_index=False).sum()

    return result_df, df1, df2


def dfs2tocsv(filepath_ds, filepath_shape, output_dir_and_name):

    # Check whether it is a dfs2 file or not
    if filepath_ds[-4:] != 'dfs2':
        print("Please pick a dfs2 file")
        return False

    # Read dfs2
    ds = mi.read(filepath_ds)

    # Check whether it is a shp file or not
    if filepath_shape[-3:] != 'shp':
        print("Please pick a shapefile")
        return False

    # Read shapefile
    shape_df = gdp.read_file(filepath_shape)

    # Check whether the file is a Polyline
    if not isinstance(shape_df['geometry'][0], LineString):
        print('The file is not a Polyline, please specify a Polyline instead.')
        return False

    index_check = 0
    # Check whether the ids are unique in the shapefile
    if len(shape_df['Id']) != shape_df['Id'].nunique():
        index_check = 1
        print('The values in the Id column in the shapefile is not unique. The sheets will be named after polyline index')

    # Get grid size
    grid_size = get_grid_size(ds)

    # Dictionary with results
    df_dict = {}

    # Loop through df with the shapefile and save the results
    for index, row in shape_df.iterrows():

        # Check direction. The calculations should always be done from left to right.
        first_coord = row['geometry'].coords[0]
        last_coord = row['geometry'].coords[len(row['geometry'].coords)-1]
    #    angle = AngleBtw2Points(first_coord, last_coord)

        # If angle is in the second or third quadrant, the general direction is right, so it must be reversed
    #    if (angle > 90) | (angle < -90):
    #        row['geometry'] = reverse_geom(row['geometry'])
        # print(
        #    'The cross section is defined from right to left. The cross section will be reversed.')
        if index_check == 1:
            df_dict[index] = get_values_for_linestring(
                grid_size, ds, row['geometry'])
        else:
            df_dict[row['Id']] = get_values_for_linestring(
                grid_size, ds, row['geometry'])

    # Create a multilevel indexed dataframe for easier read in the csv format (requested by users)
    # resultant_df = pd.concat(df_dict.values(), axis=1, keys=df_dict.keys())
    # resultant_df.to_csv(output_dir_and_name, sep=';')

    # Try with excelwriter
    with pd.ExcelWriter(output_dir_and_name) as writer:
        for key, value in df_dict.items():
            value.to_excel(writer, sheet_name=str(key))
    # return resultant_df


# if __name__ == '__main__':
#    dfs2tocsv(sys.argv[1], sys.argv[2], sys.argv[3])


filepath_ds = r'C:\Project folder\python_specialuppdrag\MASV specialuppdrag\06_Linnestaden_HPQ.dfs2'
filepath_shp = r'C:\Project folder\python_specialuppdrag\MASV specialuppdrag\test_cells.shp'
output_dir = r'C:\Project folder\python_specialuppdrag\output_csvs\heja.xls'
#test = dfs2tocsv(filepath_ds,filepath_shp)
ds = mi.read(filepath_ds)
shape_df = gdp.read_file(filepath_shp)
grid_size= get_grid_size(ds)
test,temp1,temp2= get_values_for_linestring(grid_size, ds, shape_df['geometry'][0])
#dfs2tocsv(filepath_ds,filepath_shp,output_dir)