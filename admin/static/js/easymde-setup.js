/**
 * Shared EasyMDE editor setup for the admin panel.
 * Provides: Markdown editing, image paste/drop/upload, table insertion.
 */

function createEditor(elementId, options = {}) {
    const height = options.height || 500;

    const editor = new EasyMDE({
        element: document.getElementById(elementId),
        spellChecker: false,
        autosave: { enabled: false },
        minHeight: height + 'px',
        status: ['lines', 'words', 'cursor'],
        toolbar: [
            'bold', 'italic', 'heading', '|',
            'unordered-list', 'ordered-list', '|',
            'link',
            {
                name: 'image',
                action: function(editor) { triggerImageUpload(editor); },
                className: 'fa fa-image',
                title: 'Upload Image',
            },
            {
                name: 'table',
                action: function(editor) { insertTable(editor); },
                className: 'fa fa-table',
                title: 'Insert Table',
            },
            '|',
            'quote', 'code', 'horizontal-rule', '|',
            'preview', 'side-by-side', 'fullscreen', '|',
            'undo', 'redo'
        ],
        // Render images in preview
        previewRender: function(plainText) {
            return this.parent.markdown(plainText);
        },
    });

    // --- Image paste support (Ctrl+V) ---
    editor.codemirror.on('paste', function(cm, event) {
        const items = (event.clipboardData || event.originalEvent.clipboardData).items;
        for (const item of items) {
            if (item.type.indexOf('image') !== -1) {
                event.preventDefault();
                const file = item.getAsFile();
                uploadAndInsertImage(editor, file);
                return;
            }
        }
    });

    // --- Image drag-and-drop support ---
    editor.codemirror.on('drop', function(cm, event) {
        const files = event.dataTransfer.files;
        if (files.length > 0 && files[0].type.indexOf('image') !== -1) {
            event.preventDefault();
            uploadAndInsertImage(editor, files[0]);
        }
    });

    return editor;
}

/** Upload an image file to /api/upload and insert Markdown image syntax */
function uploadAndInsertImage(editor, file) {
    const formData = new FormData();
    formData.append('upload', file);

    const cm = editor.codemirror;
    const cursor = cm.getCursor();
    cm.replaceRange('![Uploading...]()  ', cursor);

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(result => {
        if (result.url) {
            const width = prompt('Image width in pixels (leave empty for full size):', '');
            const doc = cm.getDoc();
            const content = doc.getValue();
            let imageMarkup;
            if (width && width.trim()) {
                imageMarkup = `<img src="${result.url}" alt="image" width="${width.trim()}">`;
            } else {
                imageMarkup = `![image](${result.url})`;
            }
            const newContent = content.replace('![Uploading...]()', imageMarkup);
            doc.setValue(newContent);
        } else {
            alert('Image upload failed: ' + (result.error || 'Unknown error'));
        }
    })
    .catch(err => {
        alert('Image upload failed: ' + err.message);
    });
}

/** Trigger a file picker for image upload */
function triggerImageUpload(editor) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = function() {
        if (input.files.length > 0) {
            uploadAndInsertImage(editor, input.files[0]);
        }
    };
    input.click();
}

/** Insert a Markdown table template */
function insertTable(editor) {
    const cm = editor.codemirror;
    const cursor = cm.getCursor();
    const table = '\n| Column 1 | Column 2 | Column 3 |\n| -------- | -------- | -------- |\n|          |          |          |\n|          |          |          |\n';
    cm.replaceRange(table, cursor);
}
