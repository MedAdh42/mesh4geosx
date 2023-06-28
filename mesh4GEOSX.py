from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview.util.vtkAlgorithm import smproxy, smproperty, smdomain
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataObject
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridDataWriter

# The writer for .msh files
@smproxy.writer(extensions=["xml", "vtu"], file_description="GEOSX include file; The merged blocks",
                 support_reload=False)
@smproperty.input(name="Input", port_index=0)
@smdomain.datatype(dataTypes=["vtkMultiBlockDataset"], composite_data_supported=False)
class msh2GEOSX(VTKPythonAlgorithmBase):
    """
    Simple filter that takes a MultiBlock Dataset (read from a .msh file) as input.
    outputs:
        - .vtu file containing the unstructured grid from the merged blocks and an attribute array.
        - .xml file containing the GEOSX's <Mesh> & <ElementRegions> sections defining the blocks with array.
    """
    def __init__(self):
        super().__init__(self, nInputPorts=1, nOutputPorts=0)
        self._filename = None

    @smproperty.stringvector(name="FileName", panel_visibility="never")
    @smdomain.filelist()
    def SetFileName(self, fname):
        """Specify filename for the files to write."""
        if self._filename != fname:
            self._filename = fname
            self.Modified()

    def RequestDataObject(self, request, inInfo, outInfo) -> vtkMultiBlockDataSet:
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfo.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfo, outInfo)

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)

        assert outData.IsA(inData.GetClassName())
        return 1


    def write_grid(self, request, inInfo, outInfo) -> dict:

        # get the input data
        data = self.RequestDataObject(request, inInfo, outInfo).NewInstance()
        nb_blocks = data.GetNumberOfBlocks()

        # the new grid to be constructed
        grid = vtkMultiBlockDataSet()
        grid.SetNumberOfBlocks(nb_blocks)


        # write the attribute array
        for i in range(nb_blocks):
            block = data.GetBlock(i)
            newBlock = vtkDataObject()
            if isinstance(block, vtkMultiBlockDataSet):
                nb_elements = block.GetNumberOfBlocks()
                for j in range(nb_elements):
                    element = block.GetBlock(j)
                    if block.HasMetaData(j) and not isinstance(element, vtkMultiBlockDataSet):
                        # Create a StringIO object to capture the output
                        output_string = io.StringIO()
                        # Get the metadata
                        metadata = block.GetMetaData(j)
                        # redirect towards the string
                        print(metadata, file=output_string)
                        txt = output_string.getvalue()
                        name_index = txt.find("NAME:")
                        if name_index != -1:
                            # Get the substring after "NAME:"
                            name_substring = txt[name_index + len("NAME:"):].strip()
                            # Extract the word after "NAME:"
                            name_word = name_substring.split()[0]

                        print(name_word)

