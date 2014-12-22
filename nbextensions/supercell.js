/*
Add this file to $(ipython locate)/nbextensions/supercell.js
And load it with:

require(["nbextensions/supercell"], function (supercell_extension) {
    console.log('supercell extension loaded');
    supercell_extension.load_extension();
});

*/

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/keyboard',
    'services/config',
    'notebook/js/cell',
    'notebook/js/textcell',
    'notebook/js/codecell',
    'notebook/js/outputarea',
    'notebook/js/completer',
    'notebook/js/celltoolbar',
    'codemirror/lib/codemirror',
    'codemirror/mode/python/python',
    'notebook/js/codemirror-ipython',
    'notebook/js/mathjaxutils',
    'base/js/security',
    'components/marked/lib/marked',
    'notebook/js/notebook'
], function(IPython,
    $,
    utils,
    keyboard,
    configmod,
    cellmod, 
    textcell,
    codecell,
    outputarea,
    completer,
    celltoolbar,
    CodeMirror,
    cmpython,
    cmip,
    mathjaxutils,
    security,
    marked,
    nbmod
    ) {
    var load_extension = function() {
        IPython_supercell_patch(IPython, $, marked, mathjaxutils, security, codecell, nbmod, utils, textcell, cellmod, CodeMirror);
    };

    return {
        load_extension: load_extension,
    };
})


function IPython_supercell_patch(IPython, $, marked, mathjaxutils, security, codecell, nbmod, utils, textcell, cellmod, CodeMirror) {
    // only monkey patch on notebook page
    if(!IPython.Cell) {
        return;
    }

    CodeCell = codecell.CodeCell;

    var SuperCell = function (kernel, options) {
            options = options || {};
            codecell.CodeCell.apply(this, [kernel, $.extend({}, options)]);
            this.fenced = false;
            this.dual_mode = true;
    }

    SuperCell.prototype = Object.create(codecell.CodeCell.prototype);


    SuperCell.prototype.create_element = function() {
        CodeCell.prototype.create_element.apply(this, arguments);
        var inner_cell = this.element.find('div.inner_cell');
        var render_area = $('<div/>').addClass('text_cell_render rendered_html')
            .attr('tabindex','-1');
        inner_cell.append(render_area);
        this.element.addClass('super_cell');
    }

    SuperCell.prototype.get_text = function() {
        var text = this.code_mirror.getValue();
        return text;
    };

    SuperCell.prototype.get_code = function() {
        var text = this.get_text();
        var lines = text.split('\n');
        var found_fence = false;
        this.fenced = false;
        for(var i=0; i < lines.length; i++) 
        {
            var line = lines[i];
            if (line.trim() == '```python' && lines[i+1].trim() == '#codecell') {
                this.fenced = true;
                found_fence = true;
                text = '';
                i = i+1;
                continue;
            }
            if (found_fence) {
                if (line.trim() == '```') {
                    return text;
                }
                text += '\n' + line;
            }
        }
        return text;
    };

    SuperCell.prototype.get_sections = function() {
        var text = this.code_mirror.getValue();
    }

    SuperCell.prototype.execute = function () {
        if (!this.rendered) {
            this.render();
            return;
        }
        if (!this.kernel || !this.kernel.is_connected()) {
            console.log("Can't execute, kernel is not connected.");
            return;
        }
        this.active_output_area.clear_output();

        // Clear widget area
        for (var i = 0; i < this.widget_views.length; i++) {
            var view = this.widget_views[i];
            view.remove();

            // Remove widget live events.
            view.off('comm:live', this._widget_live);
            view.off('comm:dead', this._widget_dead);
        }
        this.widget_views = [];
        this.widget_subarea.html('');
        this.widget_subarea.height('');
        this.widget_area.height('');
        this.widget_area.hide();

        this.set_input_prompt('*');
        this.element.addClass("running");
        if (this.last_msg_id) {
            this.kernel.clear_callbacks_for_msg(this.last_msg_id);
        }
        var callbacks = this.get_callbacks();
        
        var old_msg_id = this.last_msg_id;
        this.last_msg_id = this.kernel.execute(this.get_code(), callbacks, {silent: false, store_history: true});
        if (old_msg_id) {
            delete CodeCell.msg_cells[old_msg_id];
        }
        CodeCell.msg_cells[this.last_msg_id] = this;
        this.render();
        this.events.trigger('execute.CodeCell', {cell: this});
    }


    SuperCell.prototype.render = function () {
        cellmod.Cell.prototype.render.apply(this);
        var cont = true;
        this.get_code();
        if (this.fenced) {
            var that = this;
            var text = this.get_text();
            var math = null;
            var text_and_math = mathjaxutils.remove_math(text);
            text = text_and_math[0];
            math = text_and_math[1];
            marked(text, function (err, html) {
                html = mathjaxutils.replace_math(html, math);
                html = security.sanitize_html(html);
                html = $($.parseHTML(html));
                // add anchors to headings
                html.find(":header").addBack(":header").each(function (i, h) {
                    h = $(h);
                    var hash = h.text().replace(/ /g, '-');
                    h.attr('id', hash);
                    h.append(
                        $('<a/>')
                            .addClass('anchor-link')
                            .attr('href', '#' + hash)
                            .text('¶')
                    );
                });
                // links in markdown cells should open in new tabs
                html.find("a[href]").not('[href^="#"]').attr("target", "_blank");
                that.set_rendered(html);
                that.typeset();
                that.events.trigger("rendered.MarkdownCell", {cell: that});
            });
            var output = this.element.find("div.text_cell_render");
            output.show();
            this.element.find('div.input_area').hide();
        }
        return cont;
    }

    SuperCell.prototype.unrender = function () {
        if (this.read_only) return;
        var cont = cellmod.Cell.prototype.unrender.apply(this);
        if (cont) {
            this.element.find('div.input_area').show();
            var text_cell = this.element;
            var output = text_cell.find("div.text_cell_render");
            output.hide();
            if (this.get_text() === this.placeholder) {
                this.set_text('');
            }
            this.refresh();
        }
        return cont;
    };

    /**
     * @method set_rendered
     */
    SuperCell.prototype.set_rendered = function(text) {
        this.element.find('div.text_cell_render').html(text);
    };

    SuperCell.prototype.fromJSON = function (data) {
        CodeCell.prototype.fromJSON.apply(this, arguments);
        this.rendered = false;
        this.render();
    }

    // literally the only thing i changed below is instead of CodeCell, we
    // create a SuperCell. should be easier to override..
    nbmod.Notebook.prototype.insert_cell_at_index = function(type, index){

        var ncells = this.ncells();
        index = Math.min(index, ncells);
        index = Math.max(index, 0);
        var cell = null;
        type = type || this.class_config.get_sync('default_cell_type');
        if (type === 'above') {
            if (index > 0) {
                type = this.get_cell(index-1).cell_type;
            } else {
                type = 'code';
            }
        } else if (type === 'below') {
            if (index < ncells) {
                type = this.get_cell(index).cell_type;
            } else {
                type = 'code';
            }
        } else if (type === 'selected') {
            type = this.get_selected_cell().cell_type;
        }

        if (ncells === 0 || this.is_valid_cell_index(index) || index === ncells) {
            var cell_options = {
                events: this.events, 
                config: this.config, 
                keyboard_manager: this.keyboard_manager, 
                notebook: this,
                tooltip: this.tooltip
            };
            switch(type) {
            case 'code':
                cell = new SuperCell(this.kernel, cell_options);
                cell.set_input_prompt();
                break;
            case 'markdown':
                cell = new textcell.MarkdownCell(cell_options);
                break;
            case 'raw':
                cell = new textcell.RawCell(cell_options);
                break;
            default:
                console.log("Unrecognized cell type: ", type, cellmod);
                cell = new cellmod.UnrecognizedCell(cell_options);
            }

            if(this._insert_element_at_index(cell.element,index)) {
                cell.render();
                this.events.trigger('create.Cell', {'cell': cell, 'index': index});
                cell.refresh();
                // We used to select the cell after we refresh it, but there
                // are now cases were this method is called where select is
                // not appropriate. The selection logic should be handled by the
                // caller of the the top level insert_cell methods.
                this.set_dirty(true);
            }
        }
        return cell;

    };
}

