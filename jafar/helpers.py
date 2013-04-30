## some helpers

def render_pyxl(module, d, outkw):
    root, end = module.rsplit('.', 1)
    loaded = __import__(root)
    index = loaded
    for i in root.split('.')[1:] + [end]:
        index = getattr(index, i)
    return index(d).to_string()
