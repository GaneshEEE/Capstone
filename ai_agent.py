
import os
try:
    # Try newer langchain version first (1.0+)
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        # Try older langchain version (0.x)
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain.schema import HumanMessage, SystemMessage
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        print("Warning: LangChain not available. AI reasoning will use fallback mode.")
        LANGCHAIN_AVAILABLE = False
        ChatGoogleGenerativeAI = None

class AIAgent:
    def __init__(self):
        """
        Initialize LangChain agent with Google Gemini API
        """
        if not LANGCHAIN_AVAILABLE or ChatGoogleGenerativeAI is None:
            print("Warning: LangChain not available. AI reasoning will be disabled.")
            self.llm = None
            return
        
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if not api_key:
            print("Warning: GOOGLE_GEMINI_API_KEY not found. AI reasoning will be disabled.")
            self.llm = None
        else:
            print("Attempting to initialize Google Gemini API...")
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=api_key,
                    temperature=0.7
                )
                print("Google Gemini API initialized successfully!")
            except Exception as e:
                print(f"--- ERROR INITIALIZING GEMINI API ---\nModel: gemini-2.5-flash\nError: {str(e)}\n------------------------------------")
                self.llm = None
    
    def generate_summary(self, articles, company_name, context):
        """
        Generate AI-powered summary and reasoning about news impact, using historical context.
        """
        if not self.llm:
            print("AI agent not initialized. Falling back to basic summary.")
            return self._fallback_summary(articles)
        
        try:
            # Prepare article summaries - use meta description if available, otherwise title
            article_texts = []
            for i, article in enumerate(articles[:10], 1):  # Use top 10 articles
                sentiment_label = article.get('sentiment', 'neutral').upper()
                title = article.get('title', 'No title')
                summary = article.get('summary', '')
                
                # Use summary if available, otherwise just title
                if summary:
                    article_texts.append(
                        f"{i}. [{sentiment_label}] {title}\n   Summary: {summary}"
                    )
                else:
                    article_texts.append(
                        f"{i}. [{sentiment_label}] {title}"
                    )
            
            articles_text = "\n".join(article_texts)
            
            # Create prompt with historical context
            prompt = f"""Analyze the following news articles about {company_name} and provide:

<b>Summary of Key News:</b> A concise summary of the key news events (2-3 sentences).
<b>Overall Sentiment:</b> Overall sentiment assessment (positive/negative/neutral).
<b>Market Impact:</b> Potential market impact reasoning (2-3 sentences), considering any historical context provided.
<b>Key Factors to Watch:</b> Key factors investors should watch.

{context}

News Articles:
{articles_text}

Provide your analysis in a clear, professional, plain text format. For the subheadings, you MUST use <b> and </b> tags to make them bold. Do not use markdown like **. Do not start your response with any introductory phrases."""

            messages = [
                SystemMessage(content="You are an expert financial analyst. Your output must be plain text, use HTML <b> tags for bolding subheadings, and you should factor in the provided historical context in your analysis."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            return response.content
        
        except Exception as e:
            print(f"Error generating AI summary: {str(e)}")
            return self._fallback_summary(articles)

    def generate_qna_answer(self, question, context):
        """
        Generates an answer to a user's question based on historical context.
        """
        if not self.llm:
            return "The AI agent is not initialized, so I cannot answer questions right now."
        
        try:
            prompt = f"""Based on the provided historical context, answer the user's question.

Question: {question}

{context}

Provide a concise and direct answer. If the context does not contain the answer, say so. Do not make up information."""
            
            messages = [
                SystemMessage(content="You are a helpful Q&A assistant for financial analysis data. Answer the user's question based ONLY on the context provided."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"Error generating Q&A answer: {str(e)}")
            return "Sorry, I encountered an error while trying to answer the question."

    def generate_article_summary(self, article_title):
        """
        Generates a concise summary for a single news article based on its title.
        """
        if not self.llm:
            return "No summary available (AI agent not initialized)."
        
        try:
            prompt = f"""Summarize the following news article title in one concise sentence.

Article Title: {article_title}

Provide only the summary sentence, without any introductory phrases."""
            
            messages = [
                SystemMessage(content="You are a helpful assistant that summarizes news article titles concisely."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"Error generating article summary for '{article_title}': {str(e)}")
            return "No summary available (error during AI generation)."

    def _fallback_summary(self, articles):
        """
        Fallback summary when AI is not available
        """
        sentiment_counts = {
            'positive': sum(1 for a in articles if a.get('sentiment') == 'positive'),
            'negative': sum(1 for a in articles if a.get('sentiment') == 'negative'),
            'neutral': sum(1 for a in articles if a.get('sentiment') == 'neutral')
        }
        
        total = len(articles)
        if total == 0:
            return "No articles available for analysis."
        
        pos_pct = (sentiment_counts['positive'] / total) * 100
        neg_pct = (sentiment_counts['negative'] / total) * 100
        
        summary = f"Analyzed {total} news articles. "
        summary += f"Sentiment distribution: {sentiment_counts['positive']} positive ({pos_pct:.1f}%), "
        summary += f"{sentiment_counts['negative']} negative ({neg_pct:.1f}%), "
        summary += f"{sentiment_counts['neutral']} neutral ({100-pos_pct-neg_pct:.1f}%)."
        
        if pos_pct > 50:
            summary += " Overall sentiment appears positive."
        elif neg_pct > 50:
            summary += " Overall sentiment appears negative."
        else:
            summary += " Overall sentiment appears mixed."
        
        return summary
