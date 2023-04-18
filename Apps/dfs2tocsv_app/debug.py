import mikeio as mi
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gdp
from shapely.geometry import Point, LineString
import sys
from math import atan2, degrees, hypot


def get_grid_size(ds):
    # Check if quadratic grid
    if ds.geometry.dx != ds.geometry.dy:
        print('The grid is not quadratic. This might cause insufficient results')
    return ds.geometry.dx


def AngleBtw2Points(pointA, pointB):
    changeInX = pointB[0] - pointA[0]
    changeInY = pointB[1] - pointA[1]
    return degrees(atan2(changeInY, changeInX))


def get_values_for_linestring(grid_size, ds, geometry_row,direction):

    # Number of points in the polyline
    num_coords = len(geometry_row.coords)

    # Convert gridsize to integer
    grid_size = int(grid_size)

    # Always do calculation from left to right. Define the start, end and step based on general direction
    if direction == 'left':
        start = 1
        stop = num_coords
        step =1
    else:
        start = num_coords-1
        stop = 0
        step = -1

    # Loop through each coordinate, create a new polyline for each and extract result
    for j in range(start, stop,step):

        # Define start and end coordinates
        starting_coord = geometry_row.coords[j-step]
        end_coord = geometry_row.coords[j]

        # If this is the first coordinate in the linestring, create a new result_df that will later be concatenated with the other ones.
        val_dict = {}
        if j == start:
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
        # Round the length of the line to closest integer and convert
        length_of_line = int(
            np.round(Point(starting_coord).distance(Point(end_coord)), 0))

        # Create new LineString of new coordinates
        sub_line = LineString([starting_coord, end_coord])
        df_dict = {}

        # Loop thorugh the values in the dfs2 file, with the step size equivalent to the gridsize
        for i in range(0, length_of_line, grid_size):

            # Reset the values dictionary
            val_dict = {}

            # Get coordinates of point with i distance from start coordinate
            ip = sub_line.interpolate(distance=i)

            # Extract results
            point_array = ds.sel(x=ip.coords[0][0], y=ip.coords[0][1])
            time = point_array.time
            items = point_array.items
            val_dict['time'] = time

            # Extract results for each item in the dfs2
            for item in items:
                val_1 = point_array[item].values
                val_dict[str(item)] = val_1

            # Concatenate the results of the new coordinate to result_df. Note that here they are concatenated vertically
            # The vertical concatenation will be later dissolved using the groupby argument (for the time column) and taken as mean
            df_next_coord = pd.DataFrame(index=time, data=val_dict)
            df_result = pd.concat([df_result, df_next_coord])

    # df_result = df_result.groupby('time', as_index=False).mean()
    # For swedish users, the , is the default separator, instead of . (This is a feature requested by the user)
    columns = df_result.columns
    # for col in columns:
    #    df_result[col] = df_result[col].astype(
    #        str).str.replace('.', ',', regex=False)

    return df_result


def dfs2tocsv(filepath_ds, filepath_shape):

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
        print('The file is not a Polyline, please specify a PolyLine instead.')
        return False

    # Get grid size
    grid_size = get_grid_size(ds)

    # Dictionary with results
    df_dict = {}

    # Loop through df with the shapefile and save the results
    for index, row in shape_df.iterrows():

        # Check direction (from left to right, or vice versa) The calculations should always be done from left to right.
        first_coord = row['geometry'].coords[0]
        last_coord = row['geometry'].coords[len(row['geometry'].coords)]
        angle = AngleBtw2Points(first_coord,last_coord)
        #If angle is in the first or fourth quadrant, the general direction is left, else right 
        if angle<90 & angle>-90:
            direction = 'left'
        else:
            direction = 'right'

        df_dict[index] = get_values_for_linestring(
            grid_size, ds, row['geometry'],direction)

    # Create a multilevel indexed dataframe for easier read in the csv format (requested by users)
    resultant_df = pd.concat(df_dict.values(), axis=1, keys=df_dict.keys())
    # resultant_df.to_csv(output_dir_and_name, sep=';')
    return resultant_df


# if __name__ == '__main__':
#    dfs2tocsv(sys.argv[1], sys.argv[2], sys.argv[3])



filepath_ds = r'C:\Project folder\python_specialuppdrag\MASV specialuppdrag\06_Linnestaden_HPQ.dfs2'
filepath_shp = r'C:\Project folder\python_specialuppdrag\MASV specialuppdrag\endast_en.shp'
#test = dfs2tocsv(filepath_ds,filepath_shp)
ds = mi.read(filepath_ds)
shape_df = gdp.read_file(filepath_shp)
grid_size= get_grid_size(ds)
test = get_values_for_linestring(grid_size, ds, shape_df['geometry'][0],'right')