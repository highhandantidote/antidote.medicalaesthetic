document.addEventListener("DOMContentLoaded",function(){function t(t){t.forEach(t=>{t.addEventListener("click",function(t){console.log("Lead button clicked:",this.textContent.trim()),t.preventDefault();var t=this.dataset.leadId,e=this.dataset.action;console.log(`Clicked on ${e} for lead `+t),"view"===e?(console.log(`View button clicked - navigating to /lead/${t}/view`),window.location.href=`/lead/${t}/view`):"contact"===e?(console.log(`Contact button clicked - navigating to /lead/${t}/contact`),window.location.href=`/lead/${t}/contact`):"update_status"===e&&(console.log(`Update status button clicked - navigating to /lead/${t}/update_status`),window.location.href=`/lead/${t}/update_status`)})}),document.querySelectorAll(".update-lead-status-form").forEach(n=>{n.addEventListener("submit",function(e){e.preventDefault();var e=this.dataset.leadId,a=new FormData(this);if(console.log("Submitting status update for lead "+e),this.querySelector("select")&&this.querySelector("select").onchange)console.log("Form has onchange handler, using direct form submission"),this.submit();else{let t=this.action;t&&""!==t.trim()||(t=`/lead/${e}/update_status`,console.log("Constructed action URL:",t));var e=document.querySelector('meta[name="csrf-token"]')?.content,o={"X-Requested-With":"XMLHttpRequest"};e?(console.log("Found CSRF token, adding to headers"),o["X-CSRFToken"]=e):console.warn("No CSRF token found"),fetch(t,{method:"POST",body:a,headers:o}).then(t=>{if(console.log("Status update response:",t.status),t.ok)return t.json();throw new Error("Server responded with status "+t.status)}).then(t=>{console.log("Status update success:",t),t.success?(alert("Lead status updated successfully!"),window.location.reload()):alert("Error: "+(t.message||"An unknown error occurred."))}).catch(t=>{console.error("Status update error:",t),alert("An error occurred while updating the lead status. Please try again."),console.log("Attempting direct form submission as fallback"),setTimeout(()=>{n.removeEventListener("submit",arguments.callee),n.submit()},500)})}})}),t=document.querySelectorAll(".view-lead-details"),console.log(`Found ${t.length} quick view buttons`),t.forEach(t=>{t.addEventListener("click",function(){let t=this.getAttribute("data-lead-id"),a=document.getElementById("leadDetailsContent");console.log("Fetching details for lead "+t),a.innerHTML=`
                    <div class="d-flex justify-content-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                `,fetch(`/lead/${t}/details`,{method:"GET",headers:{"Content-Type":"application/json","X-Requested-With":"XMLHttpRequest"}}).then(t=>{if(t.ok)return t.json();throw new Error("Network response was not ok")}).then(t=>{var e;t.success?(e=t.lead,a.innerHTML=`
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Patient Information</h5>
                                    <table class="table table-dark">
                                        <tr>
                                            <th>Name:</th>
                                            <td>${e.patient_name}</td>
                                        </tr>
                                        <tr>
                                            <th>Contact:</th>
                                            <td>${e.mobile_number}</td>
                                        </tr>
                                        <tr>
                                            <th>Email:</th>
                                            <td>${e.email||"Not provided"}</td>
                                        </tr>
                                        <tr>
                                            <th>City:</th>
                                            <td>${e.city||"Not specified"}</td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h5>Lead Details</h5>
                                    <table class="table table-dark">
                                        <tr>
                                            <th>Procedure:</th>
                                            <td>${e.procedure_name}</td>
                                        </tr>
                                        <tr>
                                            <th>Preferred Date:</th>
                                            <td>${e.preferred_date||"Not specified"}</td>
                                        </tr>
                                        <tr>
                                            <th>Status:</th>
                                            <td><span class="badge ${(()=>{switch(e.status){case"pending":return"bg-warning";case"contacted":return"bg-info";case"scheduled":return"bg-primary";case"completed":return"bg-success";case"rejected":return"bg-danger";default:return"bg-secondary"}})()}">${e.status}</span></td>
                                        </tr>
                                        <tr>
                                            <th>Created:</th>
                                            <td>${e.created_at}</td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-12">
                                    <h5>Message</h5>
                                    <div class="p-3 bg-darker rounded">
                                        ${e.message||"No message provided"}
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-12">
                                    <h5>Actions</h5>
                                    <div class="btn-group" role="group">
                                        <a href="/lead/${e.id}/contact" class="btn btn-outline-primary">Send Message</a>
                                        <button type="button" class="btn btn-outline-success lead-status-update" data-lead-id="${e.id}" data-status="scheduled">Schedule Appointment</button>
                                        <button type="button" class="btn btn-outline-warning lead-status-update" data-lead-id="${e.id}" data-status="contacted">Mark as Contacted</button>
                                    </div>
                                </div>
                            </div>
                        `,document.querySelectorAll(".lead-status-update").forEach(t=>{t.addEventListener("click",function(){var t,e=this.getAttribute("data-lead-id"),a=this.getAttribute("data-status"),o=document.querySelector('meta[name="csrf-token"]')?.content||document.querySelector('input[name="csrf_token"]')?.value;o?((t=new FormData).append("csrf_token",o),t.append("status",a),fetch(`/lead/${e}/update_status`,{method:"POST",body:t,headers:{"X-Requested-With":"XMLHttpRequest"}}).then(t=>t.json()).then(t=>{var e;t.success?(alert("Lead status updated successfully!"),window.bootstrap&&document.getElementById("leadDetailsModal")&&(e=bootstrap.Modal.getInstance(document.getElementById("leadDetailsModal")))&&e.hide(),window.location.reload()):alert("Error: "+(t.message||"Failed to update lead status"))}).catch(t=>{console.error("Error:",t),alert("An error occurred while updating the lead status.")})):alert("CSRF token not found. Cannot update status.")})})):a.innerHTML=`
                            <div class="alert alert-danger">
                                ${t.message||"Failed to load lead details. Please try again."}
                            </div>
                        `}).catch(t=>{console.error("Error:",t),a.innerHTML=`
                        <div class="alert alert-danger">
                            Failed to load lead details. Please try again.
                        </div>
                    `})})})}var e,a;console.log("Leads.js loaded"),a=document.querySelectorAll("button, a.btn"),console.log(`Found ${a.length} total buttons on page`),a=document.querySelectorAll(".lead-action-btn"),console.log(`Found ${a.length} lead action buttons`),0===a.length?(console.log("No lead action buttons found. Trying alternative selectors..."),e=document.querySelectorAll("[data-lead-id]"),console.log(`Found ${e.length} elements with data-lead-id attribute`),0<e.length&&(console.log("Using alternative selector for lead buttons"),t(e))):t(a),document.querySelectorAll("a, button").forEach(t=>{"View"===t.textContent.trim()?(console.log("Found View button via text content, attaching handler"),t.addEventListener("click",function(t){this.dataset.leadId&&(t.preventDefault(),t=this.dataset.leadId,console.log("View button clicked for lead "+t),window.location.href=`/lead/${t}/view`)})):"Contact"===t.textContent.trim()?(console.log("Found Contact button via text content, attaching handler"),t.addEventListener("click",function(t){this.dataset.leadId&&(t.preventDefault(),t=this.dataset.leadId,console.log("Contact button clicked for lead "+t),window.location.href=`/lead/${t}/contact`)})):"Update Status"===t.textContent.trim()&&(console.log("Found Update Status button via text content, attaching handler"),t.addEventListener("click",function(t){this.dataset.leadId&&(t.preventDefault(),t=this.dataset.leadId,console.log("Update Status button clicked for lead "+t),window.location.href=`/lead/${t}/update_status`)}))})});