const SERVER_URL = "http://localhost:5001";
let serverOnline = true;

// Check server status and load locations on page load
$(document).ready(function () {
  checkServerStatus();
  loadLocations();
});

function checkServerStatus() {
  $.ajax({
    url: `${SERVER_URL}/health`,
    type: "GET",
    timeout: 5000,
    success: function (response) {
      serverOnline = true;
      $("#serverStatus")
        .removeClass("server-offline")
        .addClass("server-online")
        .html("🟢 Server Online - Ready to predict prices!");
    },
    error: function (xhr, status, error) {
      console.warn("Server health check failed:", error);
      serverOnline = false;
      $("#serverStatus")
        .removeClass("server-online")
        .addClass("server-offline")
        .html("🔴 Server Offline - Please start the Python server");
    },
  });
}

function loadLocations() {
  // Check if server is online
  if (!serverOnline) {
    $("#uiLocations").html(
      '<option value="">Server offline - Cannot load locations</option>'
    );
    return;
  }

  // Make AJAX request to fetch locations
  $.ajax({
    url: `${SERVER_URL}/get_location_names`,
    type: "GET",
    timeout: 10000, // 10-second timeout

    success: function (response) {
      console.log("Locations response:", response);

      // Handle both 'locations' and 'Locations' (case variations)
      let locations = response.locations || response.Locations;

      if (locations && Array.isArray(locations) && locations.length > 0) {
        // Default option
        let options = '<option value="" disabled selected>Choose a Location</option>';

        // Add location options
        locations.forEach(function (location) {
          let cleanLocation = location.toString().trim();
          if (cleanLocation) {
            // Escape to prevent XSS
            let escapedLocation = $("<div>").text(cleanLocation).html();
            options += `<option value="${escapedLocation}">${escapedLocation}</option>`;
          }
        });

        // Populate dropdown
        $("#uiLocations").html(options);
        console.log(`Successfully loaded ${locations.length} locations`);
      } else {
        // No locations in dataset
        $("#uiLocations").html(
          '<option value="">No locations available in dataset</option>'
        );
        console.warn("No locations found in response:", response);
      }
    },

    error: function (xhr, status, error) {
      // Specific error messages
      let errorMessage =
        status === "timeout"
          ? "Request timed out - please try again"
          : "Failed to load locations";

      console.error("Failed to load locations:", error);
      $("#uiLocations").html(`<option value="">${errorMessage}</option>`);

      // Show error in UI
      showResult(errorMessage, "error");
    },
  });
}

function getBHKValue() {
  const value = $('input[name="uiBHK"]:checked').val();
  return value ? parseInt(value) : null;
}

function getBathroomValue() {
  const value = $('input[name="uiBathrooms"]:checked').val();
  return value ? parseInt(value) : null;
}

function validateInputs(sqft, bhk, bathrooms, location) {
  const errors = [];
  
  if (!sqft || isNaN(sqft) || sqft <= 0) {
    errors.push("Please enter a valid area (square feet)");
  }
  
  if (!bhk || isNaN(bhk) || bhk <= 0) {
    errors.push("Please select number of BHK");
  }
  
  if (!bathrooms || isNaN(bathrooms) || bathrooms <= 0) {
    errors.push("Please select number of bathrooms");
  }
  
  if (!location || location.trim() === "") {
    errors.push("Please select a location");
  }
  
  return errors;
}

function onClickedEstimatePrice() {
  // Clear any previous results
  hideResult();
  
  if (!serverOnline) {
    showResult(
      "Server is offline. Please start the Python server first.",
      "error"
    );
    return;
  }

  // Get form values
  const sqft = parseFloat($("#uiSqft").val());
  const bhk = getBHKValue();
  const bathrooms = getBathroomValue();
  const location = $("#uiLocations").val();

  // Validate inputs
  const validationErrors = validateInputs(sqft, bhk, bathrooms, location);
  if (validationErrors.length > 0) {
    showResult(validationErrors.join("<br>"), "error");
    return;
  }

  // Show loading state
  const submitButton = $(".submit");
  submitButton
    .prop("disabled", true)
    .data("original-text", submitButton.html())
    .html('<span class="loading"></span> Calculating...');

  // Prepare data (matching server.py expected field names)
  const formData = {
    total_sqft: sqft,
    location: location,
    bhk: bhk,
    bath: bathrooms,
  };

  console.log("Sending prediction request:", formData);

  // Make AJAX request
  $.ajax({
    url: `${SERVER_URL}/predict_home_price`,
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify(formData),
    timeout: 15000,
    
    success: function (response) {
      console.log("Prediction response:", response);
      console.log("Response type:", typeof response);
      console.log("Response keys:", response ? Object.keys(response) : []);
      
      // Handle different possible response formats
      let estimatedPrice = null;
      
      // Check various possible property names (including the one your API actually returns)
      if (response['Estimated_Price']) {
        estimatedPrice = response['Estimated_Price'];
      } else if (response['Estimated Price']) {
        estimatedPrice = response['Estimated Price'];
      } else if (response.estimated_price) {
        estimatedPrice = response.estimated_price;
      } else if (response.estimatedPrice) {
        estimatedPrice = response.estimatedPrice;
      } else if (response.price) {
        estimatedPrice = response.price;
      } else if (response.result) {
        estimatedPrice = response.result;
      }
      
      console.log("Extracted estimated price:", estimatedPrice);
      console.log("Estimated price type:", typeof estimatedPrice);
      console.log("Estimated price truthy:", !!estimatedPrice);

      if (estimatedPrice && estimatedPrice.toString().trim() !== "") {
        let message = estimatedPrice.toString();
        
        // Add additional info if available
        if (response.inputs) {
          message += `<br><br><strong>Property Details:</strong><br>`;
          message += `Area: ${response.inputs.total_sqft} sqft<br>`;
          message += `BHK: ${response.inputs.bhk}<br>`;
          message += `Bathrooms: ${response.inputs.bath}<br>`;
          message += `Location: ${response.inputs.location}`;
        }
        
        showResult(message, "success");
      } else {
        console.error("No valid price estimate found in response:", response);
        showResult("No price estimate received from server", "error");
      }
    },
    
    error: function (xhr, status, error) {
      console.error("Prediction request failed:");
      console.error("Status:", status);
      console.error("Error:", error);
      console.error("Response text:", xhr.responseText);

      let errorMessage = "Failed to get price prediction";

      try {
        if (xhr.responseJSON) {
          const responseData = xhr.responseJSON;
          
          if (responseData.error) {
            errorMessage = responseData.error;
            if (responseData.message) {
              errorMessage += ": " + responseData.message;
            }
          } else if (responseData.message) {
            errorMessage = responseData.message;
          }

          // Show validation errors if present
          if (responseData.validation_errors && Array.isArray(responseData.validation_errors)) {
            errorMessage += "<br>Validation errors: " + responseData.validation_errors.join(", ");
          }

          // Show missing fields if present
          if (responseData.missing_fields && Array.isArray(responseData.missing_fields)) {
            errorMessage += "<br>Missing fields: " + responseData.missing_fields.join(", ");
          }
        } else if (status === "timeout") {
          errorMessage = "Request timed out. Please try again.";
        } else if (status === "error") {
          errorMessage = "Network error. Please check your connection and try again.";
        }
      } catch (e) {
        console.error("Error parsing error response:", e);
      }

      showResult(errorMessage, "error");
    },
    
    complete: function () {
      // Reset button to original state
      const submitButton = $(".submit");
      const originalText = submitButton.data("original-text") || "Estimate Price";
      submitButton.prop("disabled", false).html(originalText);
    },
  });
}

function showResult(message, type = "info") {
  console.log("=== showResult DEBUG ===");
  console.log("Message:", message);
  console.log("Type:", type);
  
  const resultDiv = $("#uiEstimatedPrice");
  
  if (resultDiv.length === 0) {
    console.error("Result div not found! Make sure #uiEstimatedPrice exists in HTML");
    return;
  }
  
  console.log("Found result div:", resultDiv.length);
  console.log("Current classes:", resultDiv.attr("class"));
  
  // Ensure message is a string
  const messageStr = message ? message.toString() : "";
  
  // Clear previous classes and add new ones
  resultDiv
    .removeClass("success error info")
    .addClass(type)
    .find("h2")
    .html(messageStr);
  
  // Show the result
  resultDiv.show();
  
  console.log("After update - classes:", resultDiv.attr("class"));
  console.log("H2 content:", resultDiv.find("h2").html());
  console.log("Div visible?", resultDiv.is(":visible"));
  console.log("=== END DEBUG ===");

  // Auto hide error messages after 10 seconds
  if (type === "error") {
    setTimeout(function () {
      hideResult();
    }, 10000);
  }
}

function hideResult() {
  const resultDiv = $("#uiEstimatedPrice");
  resultDiv.hide().removeClass("success error info");
}

// Utility function to reset form
function resetForm() {
  $("#uiSqft").val("");
  $('input[name="uiBHK"]').prop("checked", false);
  $('input[name="uiBathrooms"]').prop("checked", false);
  $("#uiLocations").val("");
  hideResult();
}

// Retry server connection every 30 seconds if offline
setInterval(function () {
  if (!serverOnline) {
    console.log("Checking server status...");
    checkServerStatus();
    if (serverOnline) {
      loadLocations();
    }
  }
}, 30000);

// Add error handling for AJAX global errors
$(document).ajaxError(function(event, xhr, settings, error) {
  if (settings.url.includes(SERVER_URL)) {
    console.error("AJAX Error for:", settings.url, error);
    serverOnline = false;
    $("#serverStatus")
      .removeClass("server-online")
      .addClass("server-offline")
      .html("🔴 Server Connection Lost");
  }
});