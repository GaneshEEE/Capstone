// Download Report Functionality

function downloadReport() {
    if (!window.lastAnalysisData) {
        alert('No analysis data available. Please analyze a stock first.');
        return;
    }

    const data = window.lastAnalysisData;
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    // Set up document
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 20;
    let yPos = margin;

    // Helper function to add text with word wrap
    function addText(text, x, y, maxWidth, fontSize = 10) {
        doc.setFontSize(fontSize);
        const lines = doc.splitTextToSize(text, maxWidth);
        doc.text(lines, x, y);
        return y + (lines.length * fontSize * 0.5);
    }

    // Helper function to check if we need a new page
    function checkNewPage(requiredSpace) {
        if (yPos + requiredSpace > pageHeight - margin) {
            doc.addPage();
            yPos = margin;
            return true;
        }
        return false;
    }

    // Title
    doc.setFontSize(20);
    doc.setFont(undefined, 'bold');
    doc.text('Stock Analysis Report', margin, yPos);
    yPos += 15;

    // Stock Info
    doc.setFontSize(16);
    doc.setFont(undefined, 'bold');
    doc.text(`${data.ticker} - ${data.company_name}`, margin, yPos);
    yPos += 10;

    doc.setFontSize(10);
    doc.setFont(undefined, 'normal');
    doc.text(`Generated: ${new Date().toLocaleString()}`, margin, yPos);
    yPos += 5;
    doc.text(`Analysis Period: ${data.timeframe}`, margin, yPos);
    yPos += 15;

    // Stock Data Section
    checkNewPage(40);
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.text('Stock Information', margin, yPos);
    yPos += 8;

    doc.setFontSize(10);
    doc.setFont(undefined, 'normal');
    if (data.stock_data) {
        doc.text(`Current Price: $${data.stock_data.current_price}`, margin, yPos);
        yPos += 6;
        doc.text(`Change: ${data.stock_data.price_change_percent >= 0 ? '+' : ''}${data.stock_data.price_change_percent}%`, margin, yPos);
        yPos += 6;
        doc.text(`Volume: ${data.stock_data.volume}`, margin, yPos);
        yPos += 6;
        doc.text(`Market Cap: ${data.stock_data.market_cap}`, margin, yPos);
        yPos += 12;
    }

    // Sentiment Analysis
    checkNewPage(50);
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.text('Sentiment Analysis', margin, yPos);
    yPos += 8;

    doc.setFontSize(10);
    doc.setFont(undefined, 'normal');
    if (data.sentiment_distribution) {
        const sentimentData = data.sentiment_distribution;
        doc.text(`Strongly Positive: ${sentimentData.strongly_positive || 0}`, margin, yPos);
        yPos += 6;
        doc.text(`Moderately Positive: ${sentimentData.moderately_positive || 0}`, margin, yPos);
        yPos += 6;
        doc.text(`Slightly Positive: ${sentimentData.slightly_positive || 0}`, margin, yPos);
        yPos += 6;
        doc.text(`Slightly Negative: ${sentimentData.slightly_negative || 0}`, margin, yPos);
        yPos += 6;
        doc.text(`Moderately Negative: ${sentimentData.moderately_negative || 0}`, margin, yPos);
        yPos += 6;
        doc.text(`Strongly Negative: ${sentimentData.strongly_negative || 0}`, margin, yPos);
        yPos += 12;
    }

    // Impact Prediction
    checkNewPage(60);
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.text('Impact Prediction', margin, yPos);
    yPos += 8;

    doc.setFontSize(10);
    doc.setFont(undefined, 'normal');
    if (data.impact_prediction && data.impact_prediction.combined) {
        const combined = data.impact_prediction.combined;
        doc.text(`Prediction: ${combined.prediction.replace(/_/g, ' ').toUpperCase()}`, margin, yPos);
        yPos += 6;
        doc.text(`Confidence: ${(combined.confidence * 100).toFixed(2)}%`, margin, yPos);
        yPos += 6;
        yPos = addText(`Reasoning: ${combined.reasoning}`, margin, yPos, pageWidth - 2 * margin);
        yPos += 12;
    }

    // AI Summary
    checkNewPage(60);
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.text('AI Summary', margin, yPos);
    yPos += 8;

    doc.setFontSize(10);
    doc.setFont(undefined, 'normal');
    if (data.ai_summary) {
        yPos = addText(data.ai_summary, margin, yPos, pageWidth - 2 * margin);
        yPos += 12;
    }

    // News Articles
    checkNewPage(40);
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.text('News Articles Analyzed', margin, yPos);
    yPos += 8;

    doc.setFontSize(9);
    doc.setFont(undefined, 'normal');
    if (data.articles && data.articles.length > 0) {
        const maxArticles = Math.min(data.articles.length, 10); // Limit to 10 articles
        for (let i = 0; i < maxArticles; i++) {
            const article = data.articles[i];
            checkNewPage(20);

            doc.setFont(undefined, 'bold');
            yPos = addText(`${i + 1}. ${article.title}`, margin, yPos, pageWidth - 2 * margin, 9);
            yPos += 2;

            doc.setFont(undefined, 'normal');
            doc.text(`Sentiment: ${article.sentiment.replace(/_/g, ' ')} (${(article.sentiment_score * 100).toFixed(1)}%)`, margin + 5, yPos);
            yPos += 5;
            doc.text(`Source: ${article.source} | Published: ${article.published}`, margin + 5, yPos);
            yPos += 8;
        }

        if (data.articles.length > 10) {
            doc.setFont(undefined, 'italic');
            doc.text(`... and ${data.articles.length - 10} more articles`, margin, yPos);
            yPos += 8;
        }
    }

    // Footer
    const totalPages = doc.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setFont(undefined, 'normal');
        doc.text(
            `Page ${i} of ${totalPages} | Generated by Stock Impact Dashboard`,
            pageWidth / 2,
            pageHeight - 10,
            { align: 'center' }
        );
    }

    // Save the PDF
    const filename = `${data.ticker}_Analysis_Report_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(filename);
}

// Show download button when analysis is complete
function showDownloadButton() {
    const downloadBtn = document.getElementById('downloadReportBtn');
    if (downloadBtn) {
        downloadBtn.style.display = 'inline-block';
    }
}

// Hide download button when starting new analysis
function hideDownloadButton() {
    const downloadBtn = document.getElementById('downloadReportBtn');
    if (downloadBtn) {
        downloadBtn.style.display = 'none';
    }
}
