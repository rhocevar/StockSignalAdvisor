from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    include_news: bool = True
    include_technicals: bool = True
    include_fundamentals: bool = True
