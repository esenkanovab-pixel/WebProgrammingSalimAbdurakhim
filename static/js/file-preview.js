document.addEventListener('DOMContentLoaded', function(){
  function humanFileSize(size){
    if(size<1024) return size+' B';
    if(size<1024*1024) return (size/1024).toFixed(1)+' KB';
    return (size/(1024*1024)).toFixed(1)+' MB';
  }

  document.querySelectorAll('input[type=file][name=attachments]').forEach(function(input){
    var preview = input.closest('form')?.querySelector('.file-previews');
    if(!preview) return;
    input.addEventListener('change', function(ev){
      preview.innerHTML = '';
      Array.from(input.files).forEach(function(file){
        var item = document.createElement('div');
        item.className = 'file-preview-item d-inline-block me-2 mb-2 text-center';
        if(file.type && file.type.startsWith('image/')){
          var img = document.createElement('img');
          img.src = URL.createObjectURL(file);
          img.onload = function(){ URL.revokeObjectURL(this.src); }
          img.className = 'img-thumbnail';
          img.style.maxWidth = '120px';
          img.style.maxHeight = '90px';
          item.appendChild(img);
          var caption = document.createElement('div');
          caption.className = 'small text-muted';
          caption.textContent = file.name + ' (' + humanFileSize(file.size) + ')';
          item.appendChild(caption);
        } else {
          var icon = document.createElement('div');
          icon.className = 'small text-muted d-block';
          icon.textContent = file.name + ' (' + humanFileSize(file.size) + ')';
          item.appendChild(icon);
        }
        preview.appendChild(item);
      });
    });
  });
});