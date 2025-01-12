document.addEventListener("DOMContentLoaded", () => {
    const queryInput = document.getElementById("query");
    const searchButton = document.getElementById("search-button");
    const helpButton = document.getElementById("help-button");
    const helpDialog = document.getElementById("help-dialog");
    const closeHelpButton = document.getElementById("close-help");
    const resultsDiv = document.getElementById("results");
  
    const verseData = {
      chapter_no: 2,
      verse_no: 47,
      sanskrit_verse: "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।\nमा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥",
      speaker: "श्री कृष्ण",
      translation: "You have a right to perform your prescribed duties, but you are not entitled to the fruits of your actions. Never consider yourself to be the cause of the results of your activities, nor be attached to inaction.",
      match_source: "translation",
      similarity_score: 0.92,
      summary: "This verse emphasizes the philosophy of selfless action (Karma Yoga). Krishna teaches Arjuna to focus on performing his duties without attachment to the results, maintaining equilibrium in both success and failure."
    };
  
    const displayVerse = (data) => {
      resultsDiv.classList.remove("hidden");
      document.getElementById("verse-header").textContent = `Chapter ${data.chapter_no}, Verse ${data.verse_no}`;
      document.getElementById("verse-speaker").textContent = `Speaker: ${data.speaker}`;
      document.getElementById("sanskrit-verse").textContent = data.sanskrit_verse;
      document.getElementById("translation").textContent = data.translation;
      document.getElementById("summary").textContent = data.summary;
      document.getElementById("match-source").textContent = data.match_source;
      document.getElementById("similarity-score").textContent = data.similarity_score.toFixed(4);
    };

    const searchVerse = async (query) => {
        try {
            const response = await fetch('http://localhost:5000/api/search', {
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
            displayVerse(data);
        } catch (error) {
            console.error('Error:', error);
            resultsDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        }
    };

    searchButton.addEventListener("click", () => {
        const query = queryInput.value.trim();
        if (!query) {
            alert('Please enter a question');
            return;
        }
        resultsDiv.classList.add("hidden");
        searchVerse(query);
    });
  
    helpButton.addEventListener("click", () => {
      helpDialog.classList.remove("hidden");
    });
  
    closeHelpButton.addEventListener("click", () => {
      helpDialog.classList.add("hidden");
    });
  });
