alert("CONTENT SCRIPT ACTIF");

function showOverlay() {
  if (document.getElementById("parental-warning")) return;

  const overlay = document.createElement("div");
  overlay.id = "parental-warning";
  overlay.style.position = "fixed";
  overlay.style.top = "0";
  overlay.style.left = "0";
  overlay.style.width = "100%";
  overlay.style.height = "100%";
  overlay.style.zIndex = "999999";
  overlay.style.display = "flex";
  overlay.style.alignItems = "center";
  overlay.style.justifyContent = "center";
  overlay.style.textAlign = "center";
  overlay.style.fontSize = "40px";
  overlay.style.color = "white";
  overlay.style.background = "rgba(255,0,0,0.85)";

  overlay.innerText = "⚠️ DANGEROUS CONTENT DETECTED";

  document.body.appendChild(overlay);
}

async function analyze(text,url) {
  console.log("debug ",url," ",text)
  const response = await fetch("http://127.0.0.1:8000/moderate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text ,url})
  });

  return await response.json();
}

async function scanPage() {
  const elements = document.querySelectorAll("p");
  let buffer = "";

  for (let el of elements) {
    if (!el.innerText) continue;

    buffer += el.innerText + " ";

    if (buffer.length >= 200) {
      const result = await analyze(buffer.slice(0, 1000), window.location.href);

      if (result.non_adequate === true) {
        showOverlay();
        return;
      }

      buffer = "";
    }
  }

  if (buffer.length > 50) {
    const result = await analyze(buffer.slice(0, 1000));
    if (result.non_adequate === true) {
      showOverlay();
    }
  }
}

setTimeout(scanPage, 3000);