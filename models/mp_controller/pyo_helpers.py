import pyomo.environ as pyo

def set_block_attribute_by_name(model, block_name, attr_name, value):
    pyo_comp = model.find_component(block_name)
    pyo_comp.__setattr__(attr_name, value)

def set_indexed_block_attribute_by_name(model, block_name, attr_name, values, index=None):
    if not index:
        index = range(len(values))
    pyo_comp = model.find_component(block_name)
    for i in index:
        pyo_comp.__getattribute__(attr_name).__setitem__(i, values[i])

def get_block_attribute_by_name(model, block_name, attr_name):
    pyo_comp = model.find_component(block_name)
    return pyo.value(pyo_comp.__getattribute__(attr_name))

def get_indexed_block_attribute_by_name(model, block_name, attr_name, index):
    pyo_comp = model.find_component(block_name)
    return pyo.value(pyo_comp.__getattribute__(attr_name)[index])

def get_all_indexed_block_attributes_by_name(model, block_name, attr_name):
    pyo_comp = model.find_component(block_name)
    return pyo.value(pyo_comp.__getattribute__(attr_name)[:])
