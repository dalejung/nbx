/*
Add this file to $(ipython locate)/nbextensions/gist.js
And load it with:
*/
define([
    'base/js/namespace',
], function (IPython) {
    var token_name = "gist_github_token";
    // dialog to request GitHub OAuth token
    // I'm not sure it's possible to step through OAuth purely client side,
    // so just ask the user to go create a token manually.
    var token_dialog = function () {
        var dialog = $('<div/>').append(
            $("<p/>")
                .html('Enter a <a href="https://github.com/settings/applications" target="_blank">GitHub OAuth token</a>:')
        ).append(
            $("<br/>")
        ).append(
            $('<input/>').attr('type','text').attr('size','40')
        );
        IPython.dialog.modal({
            title: "GitHub OAuth",
            body: dialog,
            buttons : {
                "Cancel": {},
                "OK": {
                    class: "btn-primary",
                    click: function () {
                        var token = $(this).find('input').val();
                        localStorage[token_name] = token;
                        gist_notebook();
                    }
                }
            },
            open : function (event, ui) {
                var that = $(this);
                // Upon ENTER, click the OK button.
                that.find('input[type="text"]').keydown(function (event, ui) {
                    if (event.which === 13) {
                        that.find('.btn-primary').first().click();
                        return false;
                    }
                });
                that.find('input[type="text"]').focus().select();
            }
        });
    };
    // get the GitHub token, via cookie or 
    var get_github_token = function () {
        var token = localStorage[token_name];
        if (!token) {
            token_dialog();
            return null;
        }
        return token;
    };

    var gist_notebook = function (public) {
        var gist_id = IPython.notebook.metadata.gist_id;
        var token = get_github_token();
        if (!token) {
            // dialog's are async, so we can't do anything yet.
            // the dialog OK callback will continue the process.
            console.log("waiting for auth dialog");
            return;
        }
        var method = "POST";
        var url = "https://api.github.com/gists";
        if (gist_id) {
            url = url + "/" + gist_id;
            method = "PATCH";
        }
        var filedata = {};
        var nbj = IPython.notebook.toJSON();
        nbj.nbformat = 3;
        filedata[IPython.notebook.notebook_name] = {content : JSON.stringify(nbj, undefined, 1)};
        console.log(token);
        var settings = {
            type : method,
            headers : { Authorization: "token " + token },
            data : JSON.stringify({
                public : public,
                files : filedata,
            }),
            success : function (data, status) {
                console.log("gist succeeded: " + data.id);
                IPython.notebook.metadata.gist_id = data.id;
                update_gist_link(data.id);
                IPython.notification_area.get_widget("notebook").set_message("gist succeeded: " + data.id, 1500);
                IPython.notebook.save_notebook();
            },
            error : function (jqXHR, status, err) {
                console.log(jqXHR);
                if (jqXHR.status == 403) {
                    // authentication failed,
                    // delete the cookie so that we prompt again next time
                    delete localStorage[token_name];
                }
                alert("Uploading gist failed: " + err);
            }
        };
        $.ajax(url, settings);
    };
    
    var update_gist_link = function(gist_id) {
        if (!gist_id) {
          if(IPython.notebook) {
            gist_id = IPython.notebook.metadata.gist_id;
          }
        } else {
            IPython.notebook.metadata.gist_id = gist_id;
        }
        if (!gist_id) {
            return;
        }
        var toolbar = IPython.toolbar.element;
        var link = toolbar.find("a#nbviewer");
        if ( ! link.length ) {
            link = $('<a id="nbviewer" target="_blank"/>');
            toolbar.append(
                $('<span id="nbviewer_span"/>').append(link)
            );
        }
    
        link.attr("href", "http://gist.github.com/" + gist_id);
        link.text("http://gist.github.com/" + gist_id);

        // hide buttons 
        toolbar.find('.gist-button').hide();
    };

    var gist_button = function () {
        if (!IPython.toolbar) {
            $([IPython.events]).on("app_initialized.NotebookApp", gist_button);
            return;
        }
        if ($("#gist_notebook").length === 0) {
            toolbar_button("Public Gist", function() {gist_notebook(true);});
            toolbar_button("Private Gist", function() {gist_notebook(false);});
        }
        update_gist_link();
    };

    var toolbar_button = function(text, func) {
        var btn_group = $('<div/>').addClass("btn-group gist-button");
        var button  = $('<button/>')
        button.html(text);
        button.click(func);
        btn_group.append(button);
        $(IPython.toolbar.selector).append(btn_group)
    }
    
    var load_ipython_extension = function () {
        gist_button();
        update_gist_link();
        $([IPython.events]).on("notebook_loaded.Notebook", function () {update_gist_link();});
    };
    
    return {
        load_ipython_extension : load_ipython_extension,
    };
    
});
