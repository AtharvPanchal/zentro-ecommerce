// order history interactions (simple)
document.addEventListener('DOMContentLoaded', ()=>{
  document.querySelectorAll('.list-group-item').forEach(i=>{
    i.addEventListener('click', ()=>{ /* link already navigates via anchor */ });
  });
});
