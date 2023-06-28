# vtkmodules
from vtkmodules.vtkCommonCore import vtkStringArray
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkCompositeDataSet
from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataReader, vtkXMLUnstructuredGridWriter
from vtkmodules.util import numpy_support
from paraview.modules.vtkPVVTKExtensionsMisc import vtkMergeBlocks
# other modules
from pathlib import Path
import numpy as np
from argparse import ArgumentParser
import xml.etree.ElementTree as ET


vtkTypes = [  'VTK_EMPTY_CELL', 'VTK_VERTEX', 'VTK_POLY_VERTEX', 'VTK_LINE', 'VTK_POLY_LINE', 'VTK_TRIANGLE',
              'VTK_TRIANGLE_STRIP', 'VTK_POLYGON', 'VTK_PIXEL', 'VTK_QUAD', 'VTK_TETRA', 'VTK_VOXEL',
              'VTK_HEXAHEDRON', 'VTK_WEDGE', 'VTK_PYRAMID', 'VTK_PENTAGONAL_PRISM', 'VTK_HEXAGONAL_PRISM',
              'VTK_QUADRATIC_EDGE', 'VTK_QUADRATIC_TRIANGLE', 'VTK_QUADRATIC_QUAD', 'VTK_QUADRATIC_POLYGON',
              'VTK_QUADRATIC_TETRA', 'VTK_QUADRATIC_HEXAHEDRON', 'VTK_QUADRATIC_WEDGE', 'VTK_QUADRATIC_PYRAMID',
              'VTK_BIQUADRATIC_QUAD', 'VTK_TRIQUADRATIC_HEXAHEDRON', 'VTK_TRIQUADRATIC_PYRAMID',
              'VTK_QUADRATIC_LINEAR_QUAD', 'VTK_QUADRATIC_LINEAR_WEDGE', 'VTK_BIQUADRATIC_QUADRATIC_WEDGE',
              'VTK_BIQUADRATIC_QUADRATIC_HEXAHEDRON', 'VTK_BIQUADRATIC_TRIANGLE', 'VTK_CUBIC_LINE',
              'VTK_CONVEX_POINT_SET', 'VTK_POLYHEDRON', 'VTK_PARAMETRIC_CURVE', 'VTK_PARAMETRIC_SURFACE',
              'VTK_PARAMETRIC_TRI_SURFACE', 'VTK_PARAMETRIC_QUAD_SURFACE', 'VTK_PARAMETRIC_TETRA_REGION',
              'VTK_PARAMETRIC_HEX_REGION', 'VTK_HIGHER_ORDER_EDGE', 'VTK_HIGHER_ORDER_TRIANGLE',
              'VTK_HIGHER_ORDER_QUAD', 'VTK_HIGHER_ORDER_POLYGON', 'VTK_HIGHER_ORDER_TETRAHEDRON',
              'VTK_HIGHER_ORDER_WEDGE', 'VTK_HIGHER_ORDER_PYRAMID', 'VTK_HIGHER_ORDER_HEXAHEDRON',
              'VTK_LAGRANGE_CURVE', 'VTK_LAGRANGE_TRIANGLE', 'VTK_LAGRANGE_QUADRILATERAL',
              'VTK_LAGRANGE_TETRAHEDRON', 'VTK_LAGRANGE_HEXAHEDRON', 'VTK_LAGRANGE_WEDGE',
              'VTK_LAGRANGE_PYRAMID', 'VTK_BEZIER_CURVE', 'VTK_BEZIER_TRIANGLE', 'VTK_BEZIER_QUADRILATERAL',
              'VTK_BEZIER_TETRAHEDRON', 'VTK_BEZIER_HEXAHEDRON', 'VTK_BEZIER_WEDGE', 'VTK_BEZIER_PYRAMID']

vtk_to_geosx = {'VTK_TETRA' : "tetrahedra",
                'VTK_HEXAHEDRON': "hexahedra",
                'VTK_TRIANGLE' : "triangle"}


def processMultiblockDataSet(data: vtkMultiBlockDataSet, filename: str) -> (dict, bool):
    """
    """
    # dictionary (block_id (int) : [name (str), nb_cells(int), celltypes(numpy str array)])
    mesh_info = dict()
    id = 0
    nb_cells = None
    name = None
    cell_types = None

    # Create an iterator for the vtkMultiBlockDataSet
    iterator = data.NewIterator()
    iterator.TraverseSubTreeOn()
    iterator.InitTraversal()

    # loop over blocks
    while not iterator.IsDoneWithTraversal():
        # Get the current block
        current_block = iterator.GetCurrentDataObject()
        nb_cells = current_block.GetNumberOfCells()
        cell_types = current_block.GetDistinctCellTypesArray()

        # Process the current block
        if iterator.HasCurrentMetaData():
            name = iterator.GetCurrentMetaData().Get(vtkCompositeDataSet.NAME())
            # create names array
            block_name_array = vtkStringArray()
            block_name_array.SetName("block_name")
            block_name_array.SetNumberOfValues(nb_cells)
            for i in range(nb_cells):
                block_name_array.SetValue(i, name)
            # add names array
            current_block.GetCellData().AddArray(block_name_array)
        else:
            name = None
            nb_cells = None
            cell_types = None

        # ids array
        block_id_np_array = id * np.ones(nb_cells)
        block_id_vtk_array = numpy_support.numpy_to_vtk(block_id_np_array)
        block_id_vtk_array.SetName("block_id")
        # add id array
        current_block.GetCellData().AddArray(block_id_vtk_array)

        # fill in the mesh info section
        mesh_info[id] = [name]
        mesh_info[id].append(nb_cells)
        mesh_info[id].append(numpy_support.vtk_to_numpy(cell_types))

        # Move to the next block
        iterator.GoToNextItem()
        id += 1

    # Merge the vtkMultiBlockDataSet to get a vtkUnstructuredGrid
    mergeFilter = vtkMergeBlocks()
    mergeFilter.SetInputData(data)
    mergeFilter.Update()
    # get the result of the merge
    grid = mergeFilter.GetOutput()

    # Write the grid to a file
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(filename.split(".")[0] + ".vtu")
    writer.SetInputData(grid)
    writer.Write()

    return mesh_info


def writeElementRegionXML(mesh_info: dict, outputPath: str | Path):

    # Create the root element
    root = ET.Element("ElementRegions")

    if mesh_info:
        # loop over each region
        for id in mesh_info.keys():
            name = mesh_info[id][0]
            nb_cell = mesh_info[id][2]
            cell_types = mesh_info[id][2]
            vtk_celltypes = [vtkTypes[celltype] for celltype in cell_types]
            geosx_celltypes = [vtk_to_geosx[celltype] for celltype in vtk_celltypes]
            cell_blocks = set(["_".join(str(id), celltype) for celltype in geosx_celltypes])
            # create the element
            element = ET.SubElement(root, "CellElementRegion")
            element.set("name", name)
            element.set("cellBlocks", cell_blocks)

    # Create the XML tree
    tree = ET.ElementTree(root)

    # Write the XML tree to a file
    tree.write(outputPath + ".xml", encoding="utf-8", xml_declaration=True)


# Class of superclass Exception to be raised if vtkXMLMultiBlockDataReader() encounters problems
class vtkReaderError(Exception):
    pass


def main():

    parser = ArgumentParser(prog='vtm2vtu.py',
                            description="""Converts a vtkMultiBlockDataSet to vtkUnstructuredGrid while 
                                           preserving regions (By adding 2 to cell arrays)""")
    # configure arguments
    parser.add_argument('-i', '--inputFilePath', required=True, help="Input .vtm file path", type=str)
    parser.add_argument('-o', '--outputFileName', required=True, help="Output .vtu file name", type=str)
    args = parser.parse_args()

    # get the input file as Path object
    inputPath = Path(args.inputFilePath)

    # initialize mesh info
    mesh_info = None

    try:
        if inputPath.is_file() and inputPath.suffix == ".vtm":
            # read file
            reader = vtkXMLMultiBlockDataReader()
            reader.SetFileName(args.inputFilePath)
            reader.Update()

            if reader.GetErrorCode() != 0:
                error_message = reader.GetLastError()
                raise vtkReaderError

            # get data
            data = reader.GetOutput()

            # process the data
            outputPath = str(inputPath.parent.joinpath(args.outputFileName))
            print("Writing grid in:", outputPath, ".vtu")
            mesh_info = processMultiblockDataSet(data, outputPath)

        else:
            raise FileNotFoundError

    except FileNotFoundError:
        print("The input file does not exist or is not a .vtm")

    except vtkReaderError:
        print("The following error was encountered while trying to read the file:\n", error_message)

    except PermissionError:
        print("Not authorized to write in:", str(inputPath.parent()))

    finally:
        if mesh_info:
            for id in mesh_info.keys():
                name = mesh_info[id][0]
                nb_cells = mesh_info[id][1]
                cell_types = mesh_info[id][2]
                cell_types_names = [vtkTypes[cell_type] for cell_type in cell_types]
                print("Block {}: \n\tname: \t\t{}\n\tnb cells: \t{}\n\tcell types: \t{}\n".format(id, name, nb_cells,
                                                                                                  cell_types_names))
        else:
            print("Processing aborted")


if __name__ == "__main__":
    main()