console.log("New Javascript");

const tabsBox = document.querySelector(".tabs-box");
let isDragging = false;

const dragging = (e) => {
    console.log("dragging...")
    if (!isDragging) return;
        
    tabsBox.scrollLeft -= e.movementX;
}
const dragStop = (e) => {
    isDragging = false;
        
    tabsBox.scrollLeft -= e.movementX;
}

tabsBox.addEventListener("mousedown", () => isDragging = true);
tabsBox.addEventListener("mousemove", dragging);
document.addEventListener("mouseup", dragStop);