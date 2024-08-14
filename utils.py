import numpy as np
import geopandas as gpd
from geojson import Polygon, Feature, FeatureCollection, dumps
import m2aia as m2


def central_mz_feature(imzml: m2.ImageIO.ImzMLReader, coordinates: np.ndarray, center: float, tolerance: float) -> np.ndarray:
    """Get the m/z feature of the coordinates in the MSI array image around a central m/z value

    Args:
        imzml (m2aia.ImageIO.ImzMLReader): Wrapper class for M2aia's imzML reader
        coordinates (np.ndarray): Coordinates of the spectrums pixels on the image
        center (float): Central m/z value for the feature
        tolerance (float): Tolerance for the m/z values to be considered

    Returns:
        np.ndarray: Feature of the m/z values in the coordinates
    """
    # Get the spectrum image of the m/z values that are within the tolerance of the center
    image = imzml.GetArray(center, tolerance, squeeze=True)
    
    # Transform the image into a feature
    feature = [image[y, x] for x, y in coordinates]

    return np.array(feature)


def extract_contour(mis: str) -> np.array:
    """Extract the x,y contour coordinates from the mis file

    Args:
        mis (str): The mis file

    Returns:
        coordinates: A numpy array containing the x,y coordinates of the contour
    """
    # Split the mis file by line
    mis = mis.splitlines()

    # Extract the x,y coordinates from the mis file between the lines starting with '<Point>'
    coordinates = []
    for line in mis:
        if line.startswith('<Point>'):
            # Extract the text between the tags
            point = line.split('>')[1].split('<')[0].split(',')
            # Transform the text into a list of integers
            point = [int(p) for p in point]
            # Append the point to the list
            coordinates.append(point)

    # Transform the list of points into a numpy array
    return np.array(coordinates)


def countour_to_geojson(contour: np.ndarray, save: bool = False, name: str = 'contour') -> str:
    """Transform the contour into geojson polygon.

    Args:
        contour (np.ndarray): The contour coordinates.
        save (bool, optional): If True it will save the file. Defaults to False.
        name (str, optional): The name of the file. Defaults to 'contour'.

    Returns:
        str: The geojson polygon.
    """
    # Ensure the polygon is closed by making the first and last points the same
    if not np.array_equal(contour[0], contour[-1]):
        contour = np.vstack([contour, contour[0]])

    # Create a GeoJSON Polygon
    contour_polygon = FeatureCollection([Feature(geometry=Polygon([contour.tolist()]),
                                         id="1",
                                         properties={"objectType": "contour"})])

    # Get geojson as string
    contour_geojson = dumps(contour_polygon)

    # save the results in a text if required
    if save:
        with open(f'{name}.geojson', 'w') as f:
            f.write(contour_geojson)

    return contour_geojson


def align_coord_contour(coord: np.array, contour: np.array, conserve_dimensions: bool=False) -> np.array:
    """Align and scale the coordinates to the contour.

    Args:
        coord (np.array): The coordinates to align and scale inside the contour.
        contour (np.array): The contour to align and scale the coordinates to.
        conserve_dimensions (bool, optional): If True, the area of the contour and the coordinates will be conserved. Defaults to False.

    Returns:
        np.array: The aligned and scaled coordinates.
    """
    ## Find the centroid of the contour and the coordinates
    # Ensure the polygon is closed by making the first and last points the same
    if not np.array_equal(contour[0], contour[-1]):
        contour = np.vstack([contour, contour[0]])

    # Create a GeoJSON Polygon
    contour_polygon = Polygon([contour.tolist()])

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=[contour_polygon])

    # Compute the centroid of the contour polygon
    contour_centroid = np.array(gdf.centroid[0].xy).T[0]

    # Calculate the centroid of the MALDI-MSI spectrum x,y coordinates
    coord_centroid = np.mean(coord, axis=0)


    ## Compute the scale factor
    if conserve_dimensions:
        # Compute the area of the contour polygon
        contour_area = gdf.area[0]
        
        # Distance between two consecutive coordinates
        dx = np.mean(np.unique(np.diff(np.sort(np.unique(coord[:,0])))))
        dy = np.mean(np.unique(np.diff(np.sort(np.unique(coord[:,1])))))

        # Take the dx and dy to the nearest integer
        dx = int(np.round(dx)) if abs(dx - np.round(dx)) < 0.01 else dx
        dy = int(np.round(dy)) if abs(dy - np.round(dy)) < 0.01 else dy

        # Calculate the area contained within the MALDI-MSI spectrum x,y coordinates
        coord_area = coord.shape[0] * dx * dy

        # Compute the scale factor
        scale_factor = np.sqrt(contour_area / coord_area)

    else:
        # Compute the scale factor
        scale_factor = (contour.max(axis=0) - contour.min(axis=0)) / (coord.max(axis=0) - coord.min(axis=0))


    ## Align and scale the coordinates to the contour
    # Translate coordinates to align centroids
    coord = coord - coord_centroid
    
    # Scale the coordinates to fit inside the contour
    coord = coord * scale_factor

    # Translate the coordinates back
    coord = coord + contour_centroid
    
    return coord

def coord_to_geojson(x_coord: np.ndarray, y_coord: np.ndarray, save: bool = False, name: str = 'pixels') -> str:
    """
    Transform the x,y coordinates into pixels in the form of geojson text.

    Parameters
    ----------
    x_coord : numpy.ndarray
        x coordinates (e.g., np.array([1, 2, 3])).
    y_coord : numpy.ndarray
        y coordinates (e.g., np.array([4, 5, 6])).
    save : bool
        If True it will save the file (default False).
    name : str
        If save is True it will name the file and control the directory (default 'pixels').
        The extension (.geojson) is added automaticaly.

    Returns
    -------
    str
        Feature collection, with each feature has geometry of polygon.
        Each polygon correspond to a pixel in your coordinates.

    Example
    -------
    >>> coord_to_geojson(np.array([1., 2.]), np.array([3., 4.]))
    '{"type": "FeatureCollection", "features": [{"type": "Feature", "id": "pixel(1.0, 3.0)", "geometry": {"type": "Polygon", "coordinates": [[[1.0, 3.0], [1.0, 4.0], [2.0, 4.0], [2.0, 3.0], [1.0, 3.0]]]}, "properties": {"objectType": "annotation"}}, {"type": "Feature", "id": "pixel(2.0, 4.0)", "geometry": {"type": "Polygon", "coordinates": [[[2.0, 4.0], [2.0, 5.0], [3.0, 5.0], [3.0, 4.0], [2.0, 4.0]]]}, "properties": {"objectType": "annotation"}}]}'
    """
    # Compute the distance between points
    edges_x = np.unique(np.round(np.diff(np.sort(np.unique(x_coord))), 6))
    edges_y = np.unique(np.round(np.diff(np.sort(np.unique(y_coord))), 6))
    
    # Assert if the values aren't unique and equal
    # assert edges_x == edges_y, "The distance between points on x axis and y axis are different"
    # assert edges_x.shape[0] == 1 and edges_y.shape[0] == 1, "The distance between points is not unique"
    
    # Obtain the pixel edge
    lx = edges_x[0]/2
    ly = edges_y[0]/2

    # Append a square polygon for each point in feature collection
    polygons = FeatureCollection([Feature(geometry=Polygon([[(x-lx, y-ly),
                                                             (x-lx, y+ly),
                                                             (x+lx, y+ly),
                                                             (x+lx, y-ly),
                                                             (x-lx, y-ly)]]),
                                          id=f"{i+1}",
                                          properties={"objectType": "pixel"})
                                  for i, (x, y) in enumerate(zip(x_coord, y_coord))])

    # Get geojson as string
    pixels_geojson = dumps(polygons)

    # save the results in a text if required
    if save:
        with open(f'{name}.geojson', 'w') as f:
            f.write(pixels_geojson)

    return pixels_geojson