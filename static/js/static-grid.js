document.addEventListener("DOMContentLoaded",function(){var e=document.querySelector(".scrolling-categories");if(e){e.style.animation="none",e.style.transform="none",e.style.cssText=`
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        padding: 20px;
        overflow: visible;
        height: auto;
    `;var t=Array.from(e.children);for(let e=Math.ceil(t.length/2);e<t.length;e++)t[e].remove()}});