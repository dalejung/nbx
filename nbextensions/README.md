vim bindings
============

I've had to largely disable dual mode. Having a command/edit mode for both IPython.Notebook/Cell and the vim Normal/Insert mode was too complicated for a first pass. 

Not sure if the dual mode will mesh well with what I want for vim bindings. However, that might be due to my inexperience with it. We will see. 

## Install

1. Download the `nbx/nbextensions/vim.js` to your `$IPYTHON_DIR/nbextensions` directory.
2. Edit your `$IPYTHON_DIR/$PROFILE_NAME/static/custom/custom.js` and add
```javascript
define([
    'nbextensions/gist',
    'nbextensions/vim',

], function (gist_extension,
             vim_extension
    ) {
    gist_extension.load_extension();
    vim_extension.load_extension();
});
```

## Shortcuts:

Normal Mode:

```
h,j,k,l:  :   Normal movement keys. 
shift + j :   Select cell below
shift + k :   Select cell above
meta + e  :   Execute Cell
shift + o :   Insert cell below and edit
shift + a :   Insert cell above and edit
shift + d :   Delete selected cell

meta + s  :   Save notebook
```

Insert Mode:
```
meta + e  :   Execute Cell
meta + s  :   Save notebook
```

## Notes:

* `up`/`down` movement keys will cross cell boundaries. If you at the bottom of the cell and press `down`, then you will move to the top of the next cell.
* `TextCell`s in rendered move will be treated as one line item.
