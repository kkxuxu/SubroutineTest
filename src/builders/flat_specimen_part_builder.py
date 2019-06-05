import mesh
from abaqus import *
from abaqusConstants import *

import config
from src.builders import *
from src.builders.base_builder import BaseBuilder


class FlatSpecimenPartBuilder(BaseBuilder):
    def __init__(self):
        super(FlatSpecimenPartBuilder, self).__init__()
        self._required_arguments = [
            SKETCH_NAME,
            MESH_EDGE_LENGTH,
            TARGET_MATERIAL_NAME,
            MODEL_NAME
        ]
        self._provided_arguments = [
            PART_NAME,
            SECTION_NAME,
            FULL_VOLUME_SET,
            MOVABLE_SET,
            FIXED_SET
        ]

    def _build(self, **kwargs):
        sketch_name = kwargs[SKETCH_NAME]
        mesh_edge_length = kwargs[MESH_EDGE_LENGTH]
        material_name = kwargs[TARGET_MATERIAL_NAME]
        model_name = kwargs[MODEL_NAME]
        part_name = 'Specimen_Flat_2D'
        section_name = 'Specimen_Flat_2D_section'
        full_volume_set = 'Full_%s' % part_name
        fixed_grip_set = 'Fixed_%s' % part_name
        movable_grip_set = 'Movable_%s' % part_name
        self.__create_shell_from_sketch(model_name, sketch_name, part_name)
        self.__create_partitions(model_name, part_name)
        self.__create_sets(model_name, part_name, full_volume_set, fixed_grip_set, movable_grip_set)
        self.__create_material_assignment(model_name, part_name, section_name, material_name, full_volume_set)
        self.__create_mesh(model_name, part_name, mesh_edge_length)
        self._provided_arguments_dict = {
            PART_NAME: part_name,
            SECTION_NAME: section_name,
            FULL_VOLUME_SET: full_volume_set,
            FIXED_SET: fixed_grip_set,
            MOVABLE_SET: movable_grip_set
        }

    @staticmethod
    def __create_shell_from_sketch(model_name, sketch_name, part_name):
        sketch = mdb.models[model_name].sketches[sketch_name]
        temporary_sketch = mdb.models[model_name].ConstrainedSketch(name='__profile__', sheetSize=0.2)
        temporary_sketch.sketchOptions.setValues(gridOrigin=(0.0, 0.0))
        temporary_sketch.retrieveSketch(sketch=sketch)
        part = mdb.models[model_name].Part(name=part_name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
        part.BaseShell(sketch=temporary_sketch)
        del mdb.models[model_name].sketches['__profile__']

    @staticmethod
    def __create_partitions(model_name, part_name):
        part = mdb.models[model_name].parts[part_name]
        faces = part.faces
        picked_faces = faces.getSequenceFromMask(mask=('[#1 ]',), )
        vertices, edges, datums = part.vertices, part.edges, part.datums
        part.PartitionFaceByShortestPath(point1=vertices[0], point2=vertices[9], faces=picked_faces)
        part = mdb.models[model_name].parts[part_name]
        faces = part.faces
        picked_faces = faces.getSequenceFromMask(mask=('[#2 ]',), )
        vertices, edges, datums = part.vertices, part.edges, part.datums
        part.PartitionFaceByShortestPath(point1=vertices[6], point2=vertices[9], faces=picked_faces)

    @staticmethod
    def __create_sets(model_name, part_name, full_volume_set, fixed_grip_set, movable_grip_set):
        part = mdb.models[model_name].parts[part_name]
        faces = part.faces.getSequenceFromMask(mask=('[#7 ]',), )
        part.Set(faces=faces, name=full_volume_set)
        part = mdb.models[model_name].parts[part_name]
        faces = part.faces.getSequenceFromMask(mask=('[#4 ]',), )
        part.Set(faces=faces, name=fixed_grip_set)
        part = mdb.models[model_name].parts[part_name]
        faces = part.faces.getSequenceFromMask(mask=('[#2 ]',), )
        part.Set(faces=faces, name=movable_grip_set)

    @staticmethod
    def __create_material_assignment(model_name, part_name, section_name, material_name, full_volume_set):
        mdb.models[model_name].HomogeneousSolidSection(name=section_name,
                                                       material=material_name, thickness=None)
        part = mdb.models[model_name].parts[part_name]
        region = part.sets[full_volume_set]
        part.SectionAssignment(region=region, sectionName=section_name, offset=0.0,
                               offsetType=MIDDLE_SURFACE, offsetField='',
                               thicknessAssignment=FROM_SECTION)

    @staticmethod
    def __create_mesh(model_name, part_name, mesh_edge_length):
        part = mdb.models[model_name].parts[part_name]
        part.seedPart(size=mesh_edge_length, deviationFactor=config.MESH_DEVIATION_FACTOR,
                      minSizeFactor=config.MESH_MIN_SIZE_FACTOR)
        part = mdb.models[model_name].parts[part_name]
        faces = part.faces
        picked_regions = faces.getSequenceFromMask(mask=('[#7 ]',), )
        part.setMeshControls(regions=picked_regions, elemShape=QUAD, technique=STRUCTURED)
        elem_type_quad = mesh.ElemType(elemCode=CPE4T, elemLibrary=STANDARD)
        elem_type_tri = mesh.ElemType(elemCode=CPE3T, elemLibrary=STANDARD)
        part = mdb.models[model_name].parts[part_name]
        faces = part.faces.getSequenceFromMask(mask=('[#7 ]',), )
        picked_regions = (faces,)
        part.setElementType(regions=picked_regions, elemTypes=(elem_type_quad, elem_type_tri))
        part = mdb.models[model_name].parts[part_name]
        part.generateMesh()
