/*
 * The idea here is to create custom behaviors that can be made purely with python. 
 * Or at least, purely initiated from the python side. This means that this custom
 * payload js must already be loaded.
 *
 */
define([
    'notebook/js/codecell',
    'notebook/js/notebook',
], function() {
    var load_extension = function() {
        test(IPython);
    };

    return {
        load_extension: load_extension,
    };
});

function test(IPython) {
    var CodeCell = IPython.CodeCell;
    var old_callbacks = CodeCell.prototype.get_callbacks;
    CodeCell.prototype._old_get_callbacks = old_callbacks;
    CodeCell.prototype._custom_payloads = {}
    CodeCell.prototype.get_callbacks = function () {
        var that = this;
        var callbacks = this._old_get_callbacks();
        var custom_payloads = this._custom_payloads;

        var payload_handler = $.proxy(this._handle_add_custom_payload, this);
        callbacks['shell']['payload']['add_custom_payload'] = payload_handler;

        for (var key in _custom_payloads) {
            if (!_custom_payloads.hasOwnProperty(key)) {
                continue;
            }
            callbacks['shell']['payload'][key] = function() {
                var data = {'cell': that, 'payload': payload};
                that.events.trigger('custom_' + key +'.Notebook', data);
            }
        }
        return callbacks;
    }

    CodeCell.prototype._handle_add_custom_payload = function(payload) {
        var name = payload.name;
        this.notebook.register_payload(name);
    }

    var Notebook = IPython.Notebook;
    Notebook.prototype._old_bind_events = Notebook.prototype.bind_events;
    Notebook.prototype.bind_events = function () {
        var that = this;
        this._old_bind_events()

        this.events.on('add_custom_payload.Notebook', function (event, data) {
            that.dirty = true;
        });
    }

    IPython.Notebook.prototype.register_payload = function(name, handler) {
        CodeCell.prototype._custom_payloads['dale'] = null;
        this.events.on('custom_'+name+'.Notebook', handler);
    }
}
