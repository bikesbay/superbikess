document.addEventListener("DOMContentLoaded", () => {
  const wishlistContainer = document.querySelector(".wishlist-container");

  // Function to show empty state
  function showEmptyMessage() {
    wishlistContainer.innerHTML = `
      <div class="empty-wishlist">
        <p>
          You have no bikes in your wishlist.<br />
          Click the ❤️ icon on a bike to add it here!
        </p>
      </div>
    `;
  }

  // Event delegation for remove buttons
  wishlistContainer.addEventListener("click", async (e) => {
    if (e.target.classList.contains("remove-bike")) {
      const bikeId = e.target.dataset.id;
      const card = e.target.closest(".wishlist-card");

      if (!bikeId) {
        alert("Invalid bike ID");
        return;
      }

      try {
        const response = await fetch("/remove_from_wishlist", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ bike_id: bikeId }),
        });

        const result = await response.json();
        console.log("Server response:", result);

        if (result.status === "success") {
          // Fade out effect before removing the card
          card.style.transition = "opacity 0.4s ease";
          card.style.opacity = "0";
          setTimeout(() => {
            card.remove();

            // Check if wishlist is empty after removal
            if (
              wishlistContainer.querySelectorAll(".wishlist-card").length === 0
            ) {
              showEmptyMessage();
            }
          }, 400);

          showToast("✅ Bike removed successfully!");
        } else {
          alert("❌ " + result.message);
        }
      } catch (error) {
        console.error("Error removing bike:", error);
        alert("An unexpected error occurred. Try again.");
      }
    }
  });

  // Toast Notification
  function showToast(message) {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.position = "fixed";
    toast.style.bottom = "20px";
    toast.style.right = "20px";
    toast.style.background = "#333";
    toast.style.color = "#fff";
    toast.style.padding = "10px 20px";
    toast.style.borderRadius = "8px";
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";

    document.body.appendChild(toast);

    setTimeout(() => (toast.style.opacity = "1"), 100);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  }
});
