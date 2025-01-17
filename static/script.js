document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const queryInput = document.getElementById("query");
  const searchButton = document.getElementById("search-button");
  const helpButton = document.getElementById("help-button");
  const helpDialog = document.getElementById("help-dialog");
  const closeHelpButton = document.getElementById("close-help");
  const searchModeSelect = document.getElementById("search-mode");
  const gitaResults = document.getElementById("gita-results");
  const pysResults = document.getElementById("pys-results");
  const gitaHelp = document.getElementById("gita-help");
  const pysHelp = document.getElementById("pys-help");

  const updatePlaceholder = () => {
      const mode = searchModeSelect.value;
      queryInput.placeholder = mode === 'gita' 
          ? "Ask your question about the Bhagavad Gita..." 
          : "Ask your question about the Patanjali Yoga Sutras...";
  };

  const displayResults = (data, mode) => {
      // Hide all result containers first
      gitaResults.classList.add("hidden");
      pysResults.classList.add("hidden");

      const container = mode === 'gita' ? gitaResults : pysResults;
      container.classList.remove("hidden");

      if (mode === 'gita') {
          container.querySelector(".verse-header").textContent = `Chapter ${data.chapter_no}, Verse ${data.verse_no}`;
          container.querySelector(".speaker").textContent = `Speaker: ${data.speaker}`;
          container.querySelector(".sanskrit-text").textContent = data.sanskrit_verse;
          container.querySelector(".translation").textContent = data.translation;
          container.querySelector(".commentary").textContent = data.commentary;
          container.querySelector(".summary").textContent = data.summary;
      } else {
          container.querySelector(".verse-header").textContent = `Chapter ${data.chapter_no}, Verse ${data.verse_no}`;
          container.querySelector(".sanskrit-text").textContent = data.sanskrit;
          container.querySelector(".translation").textContent = data.translation;
      }

      // Smooth scroll to results
      container.scrollIntoView({ behavior: 'smooth' });
  };

  const searchVerse = async (query, mode) => {
      try {
          const endpoint = mode === 'gita' ? '/api/search' : '/api/search_pys';
          const response = await fetch(`http://localhost:5000${endpoint}`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ query })
          });

          if (!response.ok) {
              throw new Error('Search failed');
          }

          const data = await response.json();
          displayResults(data, mode);
      } catch (error) {
          console.error('Error:', error);
          alert('Error performing search. Please try again.');
      }
  };

  // Event Listeners
  searchButton.addEventListener("click", () => {
      const query = queryInput.value.trim();
      if (!query) {
          alert('Please enter a question');
          return;
      }
      searchVerse(query, searchModeSelect.value);
  });

  searchModeSelect.addEventListener("change", () => {
      updatePlaceholder();
      gitaHelp.classList.toggle("hidden");
      pysHelp.classList.toggle("hidden");
  });

  helpButton.addEventListener("click", () => {
      helpDialog.classList.remove("hidden");
  });

  closeHelpButton.addEventListener("click", () => {
      helpDialog.classList.add("hidden");
  });

  // Close dialog when clicking outside
  helpDialog.addEventListener("click", (e) => {
      if (e.target === helpDialog) {
          helpDialog.classList.add("hidden");
      }
  });

  // Initialize placeholder
  updatePlaceholder();

  // Allow Enter key to trigger search
  queryInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
          searchButton.click();
      }
  });
});