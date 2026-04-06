from django.shortcuts import render,HttpResponse,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from stocks.models import Stock
from django.contrib.auth import logout
from django.shortcuts import redirect
import pandas as pd


import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



import requests


def HomePages(request):
      
      # ✅ Add this inside HomePages view before return statement
      news_df = pd.read_csv(os.path.join(BASE_DIR, 'merolagani_news.csv'))
      news_df = news_df.dropna(subset=["title", "date"])
      news_df["date"] = pd.to_datetime(news_df["date"], errors="coerce")
      news_df = news_df.dropna(subset=["date"]).sort_values(by="date", ascending=False)
      news_df["date"] = news_df["date"].dt.strftime("%Y-%m-%d %H:%M")
      latest_news = news_df.head(7)[["title", "date"]].to_dict(orient="records")

      top_gainers = []
      top_losers = []

    # --- Fetch Top Gainers ---
      try:
        gainers_response = requests.get("http://localhost:8001/TopGainers")
        gainers_response.raise_for_status()
        gainers_data = gainers_response.json()[:10]  # ⬅️ Limit to top 10

        for item in gainers_data:
            top_gainers.append({
                "symbol": item.get("symbol"),
                "name": item.get("securityName"),
                "price": item.get("ltp"),
                "percentage": item.get("percentageChange"),
            })
      except Exception as e:
        print("❌ Failed to fetch Top Gainers:", e)

    # --- Fetch Top Losers ---
      try:
        losers_response = requests.get("http://localhost:8001/TopLosers")
        losers_response.raise_for_status()
        losers_data = losers_response.json()[:10]  # ⬅️ Limit to top 10

        for item in losers_data:
            top_losers.append({
                "symbol": item.get("symbol"),
                "name": item.get("securityName"),
                "price": item.get("ltp"),
                "percentage": item.get("percentageChange"),
            })
      except Exception as e:
        print("❌ Failed to fetch Top Losers:", e)

      try:
        response = requests.get("http://localhost:8001/PriceVolume")
        response.raise_for_status()
        live_data = response.json()
        print("✅ Live Market Data:", live_data)  # Add this line
      except Exception as e:
        print("❌ Error fetching LiveMarket data:", e)
        live_data = []

      ticker_data = []
      for item in live_data:
        if item.get("symbol") and item.get("lastTradedPrice") is not None:
            ticker_data.append({
                "symbol": item["symbol"],
                "price": item["lastTradedPrice"],
                "change": round(item["percentageChange"], 2),
                "is_up": item["percentageChange"] >= 0
            })

      print("✅ Parsed Ticker Data:", ticker_data)  # Add this line

      context = {
        "ticker_data": ticker_data,
        "recent_news": latest_news,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
    }
      return render(request, 'home.html', context)


def news_detail(request, news_id):
    df = pd.read_csv(CSV_PATH)
    df = df.dropna(subset=["link", "title", "date"]).reset_index(drop=True)

    try:
        article_data = df.iloc[int(news_id)]
        url = article_data["link"]

        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        img_tag = soup.find("img")
        featured_image_url = img_tag['src'] if img_tag else None

        content_div = soup.find("div", id="ctl00_ContentPlaceHolder1_newsDetail")
        content_html = content_div.decode_contents() if content_div else "Content not available"

        context = {
            "article": {
                "title": article_data["title"],
                "date": article_data["date"], 
                "content": content_html,
                "image_url": featured_image_url
            }
        }

        return render(request, "news_detail.html", context)

    except Exception as e:
        return render(request, "news_detail.html", {
            "article": {
                "title": "Error loading article",
                "date": "",
                "content": f"❌ Error: {str(e)}"
            }
        })



def SignupPage(request):
    if request.method=='POST':
        uname=request.POST.get('username')
        email=request.POST.get('email')
        pass1=request.POST.get('password1')
        pass2=request.POST.get('password2')

        if pass1!=pass2:
            return HttpResponse("Your password and confrom password are not Same!!")
        else:

            my_user=User.objects.create_user(uname,email,pass1)
            my_user.save()
            return redirect('login')

    return render (request,'signup.html')

def LoginPage(request):
    if request.method=='POST':
        username=request.POST.get('username')
        pass1=request.POST.get('pass')
        user=authenticate(request,username=username,password=pass1)
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            return HttpResponse ("Username or Password is incorrect!!!")

    return render (request,'login.html')

def LogoutPage(request):
    logout(request)
    return redirect(request.META.get('HTTP_REFERER', 'home'))  # reloads same page or fallback to home




def StocksView(request):
    stocks_list = Stock.objects.all()  # ✅ Load from database instead of API

    # ✅ Paginate results (10 per page)
    paginator = Paginator(stocks_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'stocks.html', {"stocks": page_obj})  # ✅ Send database results




