document.getElementById("imageForm").addEventListener("submit", async function(e) {
    e.preventDefault();
  
    const fileInputElement = document.getElementById("fileInput");
    const file = fileInputElement.files[0];
    if (!file) {
      alert("Please select an image file.");
      return;
    }
  
    const sizesInput = document.getElementById("sizesInput").value;
    const postToTwitter = document.getElementById("postToTwitter").checked;
    const formData = new FormData();
    formData.append("file", file);
    if (sizesInput.trim() !== "") {
      formData.append("sizes", sizesInput.trim());
    }
    formData.append("post", postToTwitter ? "true" : "false");
  
    try {
      const response = await fetch("http://127.0.0.1:8000/process/", {
        method: "POST",
        body: formData
      });
      // If not authenticated, redirect to Twitter login
      if (response.status === 401) {
        window.location.href = "/login/";
        return;
      }
      const result = await response.json();
      document.getElementById("result").innerText = JSON.stringify(result, null, 2);
    } catch (error) {
      console.error("Error:", error);
      document.getElementById("result").innerText = "An error occurred while processing the image.";
    }
  });
  