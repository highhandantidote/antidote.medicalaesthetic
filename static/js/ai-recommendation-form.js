document.addEventListener("DOMContentLoaded",function(){var e=document.getElementById("addAnotherConcern");let t=document.getElementById("additionalConcerns");var n=document.getElementById("imageUploadBtn");let a=document.getElementById("imageUploadInput"),o=document.getElementById("imageFileName"),i=document.getElementById("imagePreviewContainer"),d=document.getElementById("imagePreview"),s=document.getElementById("recordAudioBtn"),c=document.getElementById("audioRecordingStatus");var l=document.getElementById("stopRecordingBtn");let r=document.getElementById("audioPlayback"),m=document.getElementById("audioData"),u=1,y,v=[];function g(){var e=new Blob(v,{type:"audio/webm"}),t=URL.createObjectURL(e);r.src=t,r.classList.remove("d-none");let n=new FileReader;n.readAsDataURL(e),n.onloadend=function(){var e=n.result;m.value=e}}e&&t&&e.addEventListener("click",function(){u++;let e=document.createElement("div");e.className="mb-3 additional-concern",e.innerHTML=`
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <label for="query_text_${u}" class="form-label fw-bold">Additional Concern</label>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-concern">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <textarea class="form-control" id="query_text_${u}" 
                    name="additional_concern_${u}" rows="3"></textarea>
            `,t.appendChild(e),e.querySelector(".remove-concern").addEventListener("click",function(){e.remove()})}),n&&a&&(n.addEventListener("click",function(){a.click(),this.classList.add("pulse-animation"),setTimeout(()=>{this.classList.remove("pulse-animation")},500)}),a.addEventListener("change",function(){var e,t;this.files&&this.files[0]?(e=this.files[0],o.textContent=e.name,(t=new FileReader).onload=function(e){d.src=e.target.result,i.classList.remove("d-none"),i.style.opacity="0",i.style.transform="translateY(10px)",setTimeout(()=>{i.style.transition="all 0.3s ease",i.style.opacity="1",i.style.transform="translateY(0)"},10)},t.readAsDataURL(e)):(o.textContent="No file chosen",i.classList.add("d-none"))}),e=document.getElementById("removeImageBtn"))&&e.addEventListener("click",function(e){e.preventDefault(),i.style.opacity="0",i.style.transform="translateY(10px)",setTimeout(()=>{i.classList.add("d-none"),a.value="",o.textContent="No file chosen"},300)}),s&&l&&(s.addEventListener("click",function(){v=[],navigator.mediaDevices.getUserMedia({audio:!0}).then(e=>{c.classList.remove("d-none"),s.classList.add("disabled"),(y=new MediaRecorder(e)).ondataavailable=e=>{v.push(e.data)},y.onstop=g,y.start()}).catch(e=>{console.error("Error accessing microphone:",e),alert("Could not access your microphone. Please check permissions and try again.")})}),l.addEventListener("click",function(){y&&"inactive"!==y.state&&(y.stop(),s.classList.remove("disabled"),c.classList.add("d-none"))}));n=document.createElement("style");n.textContent=`
        .recording-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background-color: #dc3545;
            border-radius: 50%;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }
    `,document.head.appendChild(n)});