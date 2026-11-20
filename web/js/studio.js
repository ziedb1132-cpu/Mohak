const statusEl=document.getElementById("render-status");
const renderBtn=document.getElementById("render-btn");
const video=document.getElementById("video");
const empty=document.getElementById("empty-preview");
async function loadEpisodes(){
  try{
    const response=await fetch("/api/episodes");
    if(!response.ok) throw new Error("API unavailable");
    const episodes=await response.json();
    const list=document.getElementById("scene-list");
    list.innerHTML="";
    episodes[0].scenes.forEach((scene,index)=>{
      const row=document.createElement("div");row.className="scene-row";
      const number=document.createElement("b");number.textContent=String(index+1).padStart(2,"0");
      const info=document.createElement("div");const title=document.createElement("strong");title.textContent=scene.title;
      const meta=document.createElement("small");meta.textContent=scene.duration+" ثوانٍ · "+scene.status;
      info.append(title,meta);row.append(number,info);list.append(row);
    });
  }catch{statusEl.textContent="واجهة العرض جاهزة؛ شغّل خادم Python لتحميل بيانات المشروع.";}
}
renderBtn.addEventListener("click",async()=>{
  renderBtn.disabled=true;renderBtn.textContent="جارٍ تجهيز الرندر…";
  statusEl.textContent="يتم تشغيل Blender. قد تستغرق العملية عدة دقائق.";
  try{
    const response=await fetch("/api/render",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({episode_id:"episode_001"})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error||"Render failed");
    video.src=data.video_url;video.style.display="block";empty.style.display="none";
    statusEl.textContent="اكتمل الرندر بنجاح.";
  }catch(error){statusEl.textContent=error.message+" — يمكن تشغيل الرندر من GitHub Actions أيضاً.";}
  finally{renderBtn.disabled=false;renderBtn.textContent="إنتاج المشهد التجريبي";}
});
loadEpisodes();
