document.addEventListener("DOMContentLoaded", function() {
    var sdk = apigClientFactory.newClient({
      apiKey: "tncDcRrOu55tOieRLVJipj9LDR87sQm3ZQpIlULg"
    });

    var searchButton = document.getElementById("search-button");
    searchButton.addEventListener("click", function() {
      var searchInput = document.getElementById("search-input");
      var searchTerm = searchInput.value;
      loadImages(searchTerm);
    });

    function loadImages(searchTerm) {
      var params = {
        q: searchTerm
      };

      sdk.searchGet(params, null)
        .then(function(response) {
          var results = response.data.results;
          var photoContainer = document.getElementById("photo-container");
          photoContainer.innerHTML = ""; // Clear previous results

          results.forEach(function(result) {
            var imgUrl = result.url;
            var labels = result.labels;
          
            var imgElement = document.createElement("img");
            imgElement.src = imgUrl;
            imgElement.className = "img-responsive"; // Add Bootstrap responsive class for styling
          
            var labelElement = document.createElement("div");
            labelElement.textContent = labels.join(", ");
            labelElement.className = "image-labels"; // Add a custom class for styling
          
            var container = document.createElement("div");
            container.className = "col-md-4"; // Add Bootstrap column class for styling
            container.appendChild(imgElement);
            container.appendChild(labelElement);
          
            photoContainer.appendChild(container);
          });
          
        })
        .catch(function(error) {
          console.error("Error loading images:", error);
        });
    }

    function uploadImage(file, labels) {
        var headers = {
          "x-amz-meta-customLabels": labels,
          "filename": file.name,
          "x-api-key": "tncDcRrOu55tOieRLVJipj9LDR87sQm3ZQpIlULg",
        };
      
        fetch("https://6p798c9be7.execute-api.us-east-1.amazonaws.com/prod/upload", {
          method: "PUT",
          headers: headers,
          body: file,
        })
          .then(function (response) {
            if (response.ok) {
              console.log("Image uploaded successfully:", response);
              alert("Image uploaded successfully!");
              document.getElementById("image-upload").value = "";
              document.getElementById("upload-headers-input").value = "";
            } else {
              throw new Error("Failed to upload image");
            }
          })
          .catch(function (error) {
            console.error("Error uploading image:", error);
            alert("Error uploading image: " + error);
          });
      }
    
      // Handle the upload button click
      document.getElementById("upload-button").addEventListener("click", function () {
        var fileInput = document.getElementById("image-upload");
        var headersInput = document.getElementById("upload-headers-input");
        if (fileInput.files.length > 0) {
          var labels = headersInput.value.split(",").map(function (label) {
            return label.trim();
          });
          uploadImage(fileInput.files[0], labels);
        } else {
          alert("Please select an image to upload.");
        }
      });

    let recognition = null;
    let isRecording = false;
    let micButton = document.getElementById("transcribe-button");

    micButton.addEventListener("click", function () {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
    });

    function startRecording() {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = "en-US";
        recognition.onresult = function (event) {
          var query = event.results[0][0].transcript;
          console.log("Query: " + query);
          document.getElementById("search-input").value = query;
        };
        recognition.start();
        isRecording = true;
        micButton.textContent = "Stop Recording";
    }
      
    function stopRecording() {
        if (recognition) {
            recognition.stop();
            console.log("Stopped recording");
            isRecording = false;
            micButton.textContent = "Start Recording";
        }
    }


  });