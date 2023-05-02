import mikeio as mi
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gdp
from shapely.geometry import Point, LineString
import sys
from math import atan2, degrees, hypot
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


def AngleBtw2Points(pointA, pointB):
    changeInX = pointB[0] - pointA[0]
    changeInY = pointB[1] - pointA[1]
    return degrees(atan2(changeInY, changeInX))


def calculate_flow_direction(perpendicular_angle, col):
    if (col > perpendicular_angle-90) & (col < perpendicular_angle+90):
        return True
    else:
        return False


def calculate_flow_magnitude(df, grid_size, sub_line):
    # Get the columns of the df. The two columns that will be used for further calculations are the P flux (flow in x direction, index = 2) and Q Flux (flow in y direction, index = 3).
    columns = df.columns

    # Resultant flow is given by hypothenuse of both. Note that the flow is given in per meter, meaning that we need to multiply by the grid size
    df['Discharge [meter^3/s]'] = df.apply(
        lambda x: hypot(x[columns[3]], x[columns[2]]), axis=1)
    df['Discharge [meter^3/s]'] = df['Discharge [meter^3/s]'] * grid_size
    df['flow_direction'] = df.apply(lambda x: degrees(
        atan2(x[columns[3]], x[columns[2]])), axis=1)

    # Get the coordinates of the
    coord_list = list(sub_line.coords)
    start_coord = coord_list[0]
    end_coord = coord_list[1]
    angle_line = AngleBtw2Points(start_coord, end_coord)
    perpendicular_line = angle_line - 90

    # Update the columns, and calculate flow direction
    columns = df.columns
    df['Discharge [meter^3/s]'] = df.apply(lambda x: x[columns[4]] if calculate_flow_direction(
        perpendicular_line, x[columns[5]]) else x[columns[4]]*-1, axis=1)
    df['Discharge + [meter^3/s]'] = df.apply(
        lambda x: x[columns[4]] if x[columns[4]] > 0 else 0, axis=1)
    df['Discharge - [meter^3/s]'] = df.apply(
        lambda x: x[columns[4]] if x[columns[4]] < 0 else 0, axis=1)

    # Calculate the cumulative sum of the flows
    df['Cum. disc. + [meter^3]'] = np.cumsum(df['Discharge + [meter^3/s]'])
    df['Cum. disc. - [meter^3]'] = np.cumsum(df['Discharge - [meter^3/s]'])
    df['Cum. disc. [meter^3/s]'] = np.cumsum(df['Discharge [meter^3/s]'])
    return df[['time','Discharge + [meter^3/s]', 'Discharge - [meter^3/s]', 'Discharge [meter^3/s]', 'Cum. disc. + [meter^3]', 'Cum. disc. - [meter^3]', 'Cum. disc. [meter^3/s]']]


def get_values_for_linestring(grid_size, ds, geometry_row):

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
        # Create new LineString of new coordinates
        sub_line = LineString([starting_coord, end_coord])

        # If this is the first coordinate in the linestring, create a new result_df that will later be concatenated with the other ones.
        val_dict = {}
        if j == 1:
            # Extract results
            point_array = ds.sel(x=starting_coord[0], y=starting_coord[1])
            time = point_array.time
            items = point_array.items
            val_dict['time'] = time

            # Extract results for each item in the dfs2
            for item in items:
                val_1 = point_array[item].values
                val_dict[str(item)] = val_1
            df_result = pd.DataFrame(index=time, data=val_dict)
            df_result = calculate_flow_magnitude(
                df_result, grid_size, sub_line)
            # Add the coordinates of point_array to our memory list
            calculated_coords.append(
                [point_array.geometry.x, point_array.geometry.y])

        # Round the length of the line to closest integer and convert
        length_of_line = int(
            np.round(Point(starting_coord).distance(Point(end_coord)), 0))

        # Loop thorugh the values in the dfs2 file, with the step size equivalent to the gridsize
        for i in range(0, length_of_line, grid_size):

            # Reset the values dictionary
            val_dict = {}

            # Get coordinates of point with i distance from start coordinate
            ip = sub_line.interpolate(distance=i)

            # Extract results from point
            point_array = ds.sel(x=ip.coords[0][0], y=ip.coords[0][1])

            # Check whether the point have been calculated before
            new_coord_list = [point_array.geometry.x, point_array.geometry.y]
            if new_coord_list not in calculated_coords:

                # Extract values and time
                time = point_array.time
                items = point_array.items
                val_dict['time'] = time

                # append the coordinates to calculated_coords
                calculated_coords.append(new_coord_list)

                # Extract results for each item in the dfs2
                for item in items:
                    val_1 = point_array[item].values
                    val_dict[str(item)] = val_1

                # Create a df with this cross sections values
                df_next_coord = pd.DataFrame(index=time, data=val_dict)

                # Calculate flow magnitude and its direction
                df_next_coord = calculate_flow_magnitude(
                    df_next_coord, grid_size, sub_line)
                # Concatenate the results of the new coordinate to result_df. Note that here they are concatenated vertically

                # The vertical concatenation will be later dissolved using the groupby argument (for the time column) and taken as mean

                df_result = pd.concat([df_result, df_next_coord])

    # TEST! Include last coord.
    # Extract results
    point_array = ds.sel(x=end_coord[0], y=end_coord[1])
    time = point_array.time
    items = point_array.items
    val_dict['time'] = time
    new_coord_list = [point_array.geometry.x, point_array.geometry.y]

    if new_coord_list not in calculated_coords:
        # Extract results for each item in the dfs2
        # print("Du missade sista!!!")
        for item in items:
            val_1 = point_array[item].values
            val_dict[str(item)] = val_1
        df_next = pd.DataFrame(index=time, data=val_dict)
        df_next_coord = calculate_flow_magnitude(
            df_next, grid_size, sub_line)
        # Add the coordinates of point_array to our memory list
        df_result = pd.concat([df_result, df_next_coord])
        calculated_coords.append(new_coord_list)

    df_result = df_result.groupby('time', as_index=False).sum()
    # For swedish users, the , is the default separator, instead of . (This is a feature requested by the user)
    #columns = df_result.columns
    #for col in columns:
    #    df_result[col] = df_result[col].astype(
    #        str).str.replace('.', ',', regex=False)

    return df_result


def dfs2toxlss(filepath_ds, filepath_shape,output_dir_and_name):

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
    #Check whether the ids are unique in the shapefile
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
        angle = AngleBtw2Points(first_coord, last_coord)

        # If angle is in the second or third quadrant, the general direction is right, so it must be reversed
        if (angle > 90) | (angle < -90):
            row['geometry'] = reverse_geom(row['geometry'])
            #print(
            #    'The cross section is defined from right to left. The cross section will be reversed.')
        if index_check == 1:
            df_dict[index] = get_values_for_linestring(
                grid_size, ds, row['geometry'])
        else:
            df_dict[row['Id']] = get_values_for_linestring(
                grid_size, ds, row['geometry'])
        

    # Create a multilevel indexed dataframe for easier read in the csv format (requested by users)

    #Try with excelwriter
    with pd.ExcelWriter(output_dir_and_name) as writer:
        for key, value in df_dict.items():
            value.to_excel(writer,sheet_name=str(key))
    #return resultant_df


# if __name__ == '__main__':
#    dfs2tocsv(sys.argv[1], sys.argv[2], sys.argv[3])
