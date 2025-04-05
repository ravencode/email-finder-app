document.addEventListener('DOMContentLoaded', function() {
    const scanForm = document.getElementById('scan-form');
    const scanningStatus = document.getElementById('scanning-status');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    // Handle scan form submission
    if (scanForm) {
        scanForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const urlsTextarea = document.getElementById('urls');
            const urls = urlsTextarea.value.trim().split('\n').filter(url => url.trim() !== '');
            
            if (urls.length === 0) {
                alert('Please enter at least one website URL');
                return;
            }
            
            // Show scanning status
            scanningStatus.classList.remove('d-none');
            document.getElementById('scan-btn').disabled = true;
            
            // Start the scan
            startScan(urls);
        });
    }
    
    // If we're on the results page, load results
    if (typeof scanId !== 'undefined') {
        loadResults();
    }
    
    function startScan(urls) {
        fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ urls: urls.join('\n') })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // Poll for progress
            pollScanProgress(data.scan_id);
        })
        .catch(error => {
            console.error('Error starting scan:', error);
            alert('Failed to start scan. Please try again.');
        });
    }
    
    function pollScanProgress(scanId) {
        const poll = setInterval(() => {
            fetch(`/api/scan-status/${scanId}`)
                .then(response => response.json())
                .then(data => {
                    updateProgressUI(data);
                    
                    if (data.status === 'completed') {
                        clearInterval(poll);
                        window.location.href = `/results/${scanId}`;
                    }
                })
                .catch(error => {
                    console.error('Error polling scan status:', error);
                    clearInterval(poll);
                });
        }, 1000);
    }
    
    function updateProgressUI(data) {
        const percent = data.progress;
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `Processed ${data.completed} of ${data.total} websites`;
    }
    
    function loadResults() {
        fetch(`/api/scan-status/${scanId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    renderResults(data.results);
                } else {
                    // If still scanning, poll for updates
                    setTimeout(() => loadResults(), 1000);
                }
            })
            .catch(error => {
                console.error('Error loading results:', error);
                document.getElementById('loading-message').textContent = 'Error loading results. Please try again.';
            });
    }
    
    function renderResults(results) {
        const loadingMessage = document.getElementById('loading-message');
        const resultsContainer = document.getElementById('results-container');
        const resultsBody = document.getElementById('results-body');
        
        loadingMessage.classList.add('d-none');
        resultsContainer.classList.remove('d-none');
        
        // Clear previous results
        resultsBody.innerHTML = '';
        
        // Sort URLs alphabetically
        const sortedUrls = Object.keys(results).sort();
        
        for (const url of sortedUrls) {
            const result = results[url];
            const row = document.createElement('tr');
            
            // Website column
            const urlCell = document.createElement('td');
            urlCell.textContent = url;
            row.appendChild(urlCell);
            
            // Emails column
            const emailsCell = document.createElement('td');
            if (result.emails.length > 0) {
                const emailsCount = document.createElement('div');
                emailsCount.classList.add('mb-1');
                emailsCount.innerHTML = `<strong>${result.emails.length}</strong> email${result.emails.length > 1 ? 's' : ''} found`;
                emailsCell.appendChild(emailsCount);
                
                const emailsList = document.createElement('div');
                result.emails.slice(0, 3).forEach(email => {
                    const emailBadge = document.createElement('span');
                    emailBadge.classList.add('email-badge');
                    emailBadge.textContent = email;
                    emailsList.appendChild(emailBadge);
                });
                
                if (result.emails.length > 3) {
                    const moreBadge = document.createElement('span');
                    moreBadge.classList.add('email-badge');
                    moreBadge.textContent = `+${result.emails.length - 3} more`;
                    emailsList.appendChild(moreBadge);
                }
                
                emailsCell.appendChild(emailsList);
            } else {
                emailsCell.textContent = 'No emails found';
            }
            row.appendChild(emailsCell);
            
            // Status column
            const statusCell = document.createElement('td');
            const statusBadge = document.createElement('span');
            statusBadge.classList.add('badge', 'rounded-pill');
            
            if (result.status === 'success') {
                statusBadge.classList.add('bg-success');
                statusBadge.textContent = 'Success';
            } else {
                statusBadge.classList.add('bg-danger');
                statusBadge.textContent = 'Failed';
            }
            
            statusCell.appendChild(statusBadge);
            row.appendChild(statusCell);
            
            // Add row click event to show details
            row.addEventListener('click', () => showDetails(url, result));
            
            resultsBody.appendChild(row);
        }
    }
    
    function showDetails(url, result) {
        const detailsCard = document.getElementById('details-card');
        const detailUrl = document.getElementById('detail-url');
        const logDetails = document.getElementById('log-details');
        
        detailsCard.classList.remove('d-none');
        detailUrl.textContent = url;
        
        // Clear previous logs
        logDetails.innerHTML = '';
        
        // Add logs
        result.logs.forEach(log => {
            const logEntry = document.createElement('div');
            logEntry.classList.add('log-entry');
            
            if (log.startsWith('✅')) {
                logEntry.classList.add('success');
            } else if (log.startsWith('❌')) {
                logEntry.classList.add('error');
            } else if (log.startsWith('⚠️')) {
                logEntry.classList.add('warning');
            } else {
                logEntry.classList.add('info');
            }
            
            logEntry.textContent = log;
            logDetails.appendChild(logEntry);
        });
        
        // Scroll to details
        detailsCard.scrollIntoView({ behavior: 'smooth' });
    }
});