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

  // Validate DOM elements
  if (!queryInput || !searchButton || !helpButton || !helpDialog || !closeHelpButton || 
      !searchModeSelect || !gitaResults || !pysResults || !gitaHelp || !pysHelp) {
    console.error('Required DOM elements not found');
    return;
  }

  const updatePlaceholder = () => {
      const mode = searchModeSelect.value;
      queryInput.placeholder = mode === 'gita' 
          ? "Ask your question about the Bhagavad Gita..." 
          : "Ask your question about the Patanjali Yoga Sutras...";
  };

  const handleIrrelevantQuery = (data) => {
    const irrelevantContainer = document.getElementById("irrelevant-results") || 
      document.createElement("div");
    
    irrelevantContainer.id = "irrelevant-results";
    irrelevantContainer.className = "results-container";
    
    if (!irrelevantContainer.parentNode) {
      document.querySelector(".container").appendChild(irrelevantContainer);
    }

    irrelevantContainer.innerHTML = `
      <div class="result">
          <div class="section">
              <h3>🤔 Query Outside Scope</h3>
              <p>${data.message}</p>
              <h4>Try asking questions like:</h4>
              <ul>
                  ${data.examples.map(example => `<li>${example}</li>`).join('')}
              </ul>
          </div>
      </div>
    `;
    irrelevantContainer.classList.remove("hidden");
    irrelevantContainer.scrollIntoView({ behavior: 'smooth' });
  };

  const displayResults = (data, mode) => {
      // Hide all result containers first
      gitaResults.classList.add("hidden");
      pysResults.classList.add("hidden");

      const irrelevantContainer = document.getElementById("irrelevant-results");
      if (irrelevantContainer) {
        irrelevantContainer.classList.add("hidden");
      }

      if (data.is_irrelevant) {
        handleIrrelevantQuery(data);
        return;
      }

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
          searchButton.disabled = true;
          queryInput.disabled = true;
          
          const endpoint = mode === 'gita' ? '/api/search' : '/api/search_pys';
          const response = await fetch(`http://localhost:5000${endpoint}`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ query })
          });

          if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          displayResults(data, mode);
      } catch (error) {
          console.error('Error:', error);
          alert('Error performing search. Please try again.');
      } finally {
          searchButton.disabled = false;
          queryInput.disabled = false;
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