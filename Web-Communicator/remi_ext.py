import remi.gui as gui

class FoldButton(gui.Button):
    def __init__(self, *args, **kwargs):
        super(FoldButton, self).__init__('-', *args, **kwargs)
        self.nested_rows = []
        self.onclick.connect(self.clicked)

    def add_nested_row(self, r):
        self.nested_rows.append(r)
        r.style['display'] = 'table-row'

    def clicked(self, emitter):
        r = None
        for r in self.nested_rows:
            r.style['display'] = 'none' if r.style['display']=='table-row' else 'table-row'
            if 'fold' in r.children['fold_cell_0'].children.keys():
                r.children['fold_cell_0'].children['fold'].clicked(None)
        self.set_text('-' if r.style['display']=='table-row' else '+')


class TreeTable(gui.Table):
    def __init__(self, max_fold_levels=10, *args, **kwargs):
        """
        Args:
            kwargs: See Widget.__init__()
        """
        super(TreeTable, self).__init__(*args, **kwargs)
        self.fold_level = 0
        self.max_fold_levels = max_fold_levels
        self.current_fold_button = {}

    def append_row(self, value, key=''):
        modified_row = gui.TableRow(style={'display':'table-row'})
        fold_items = ['']*(self.fold_level+1)
        for i in range(0, len(fold_items)):
            ti = gui.TableItem(fold_items[i])
            ti.style['min-width'] = '10px'
            modified_row.append(ti, "fold_cell_%s"%i)
        
        for k in value._render_children_list:
            modified_row.append(value.children[k], k)

        modified_row.children[modified_row._render_children_list[self.fold_level+1]].attributes['colspan'] = str(self.max_fold_levels - self.fold_level)

        if self.fold_level>0:
            self.current_fold_button[str(self.fold_level)].add_nested_row(modified_row)
        self.current_row = modified_row
        return super(gui.Table, self).append(modified_row, key)

    def append(self, value, key=''):
        keys = self.append_row(value, key)
        if type(value) in (list, tuple, dict):
            for k in keys:
                self.children[k].on_row_item_click.connect(self.on_table_row_click)
        else:
            value.on_row_item_click.connect(self.on_table_row_click)
        return keys

    def begin_fold(self):
        self.fold_level = min(self.fold_level + 1, self.max_fold_levels)
        self.current_fold_button[str(self.fold_level)] = FoldButton(width = 15, height = 15)
        self.current_row.children['fold_cell_0'].append(self.current_fold_button[str(self.fold_level)], 'fold')
        txt = self.current_row.children['fold_cell_0'].get_text()
        self.current_row.children['fold_cell_0'].remove_child(self.current_row.children['fold_cell_0'].children['text'])
        self.current_row.children['fold_cell_0'].set_text(txt)

    def end_fold(self):
        self.fold_level = max(0, self.fold_level - 1)
        if self.fold_level == 0:
            self.current_fold_button = None