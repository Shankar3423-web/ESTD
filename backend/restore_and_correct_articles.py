import asyncio
import hashlib
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(r"c:\Users\nered\Desktop\ESTD\backend")
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from sqlalchemy import text
from backend.database.connection.session import get_db_session
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step3_content_cleaning.services.content_cleaning_service import ContentCleaningService
from backend.step4_duplicate_detection.normalizers.url_normalizer import normalize_url

ARTICLES_DATA = [
    {
        "id": 495,
        "title": 'Beta Film Secures Major Deals for Female-Led Dramas "Queen Silvia" and "La Vida Barcelona"',
        "url": "https://variety.com/2026/tv/global/beta-film-queen-silvia-la-vida-barcelona-1236908698/",
        "source": "Variety",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "TV & OTT",  # Resolved to TV & OTT per Phase D
        "subcategory_id": 3,
        "published_at": "2026-10-12T06:28:01Z",
        "doc_id": "1jvO_6pY_mq6UKLukLHPflxhWuS9gf5PZwYs_5tlJ6ew",
        "doc_title": 'ESTD - Beta Film Secures Key Broadcast Deals for "Queen Silvia" and "La Vida Barcelona"',
        "sub_folder_id": "1HWXIXZI29cTXmXXx8ZN_d_F78bV8bLw_"
    },
    {
        "id": 496,
        "title": "Princess Diana Series With Unheard Audio Sells To Prime Video",
        "url": "https://deadline.com/2026/10/princess-diana-unheard-audio-series-prime-video-1237151052/",
        "source": "Deadline",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "TV & OTT",
        "subcategory_id": 3,
        "published_at": "2026-10-12T06:00:53Z",
        "doc_id": "1NoVpCTZQQRFUGeZfMAqUemr2XZdmge7jtxNgn3E2FIk",
        "doc_title": "ESTD - Prime Video Secures UK & Ireland Rights for 'Diana: Her Secret Confessions' Docuseries",
        "sub_folder_id": "1HWXIXZI29cTXmXXx8ZN_d_F78bV8bLw_"
    },
    {
        "id": 497,
        "title": "Chappell Roan Shines at Abbey in Latex Ensemble Paired with Thigh-High Socks and Pumps",
        "url": "https://wwd.com/footwear-news/shoe-trends/chappell-roan-abbey-pumps-socks-1239342186/",
        "source": "WWD",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Celebrities & Pop Culture",
        "subcategory_id": 5,
        "published_at": "2026-10-11T18:49:11Z",
        "doc_id": "1WjGie56hhB4MAfJvUGCsQEQH6ki8hgBuX-JUMFdGnsQ",
        "doc_title": "ESTD - Chappell Roan Dazzles in Latex and Thigh-High Socks at National PrEP Day Event",
        "sub_folder_id": "1P8T3mU45xGk5j4cI2aI2g92P8-v725A-"
    },
    {
        "id": 498,
        "title": "KKIRO Newsradio Gives Away Tickets to Terry Fator's Live Performance at Muckleshoot Casino Resort",
        "url": "https://us.headtopics.com/news/kkiro-newsradio-gives-away-tickets-to-terry-fator-s-live-88699165",
        "source": "Head Topics",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Music",  # Documented Music with promotional contest review per Phase D
        "subcategory_id": 2,
        "published_at": "2026-10-11T19:17:00Z",
        "doc_id": "1bw47QfnFxh0VT0W7HaSa2MxDBPqkwYhRtVo-36SgUQM",
        "doc_title": "ESTD - KIRO Newsradio Offers Free Tickets to Terry Fator's Live Performance at Muckleshoot Casino",
        "sub_folder_id": "1bq69bTTu12-5UqPOyuZLkh88y5Uq0A2F"
    },
    {
        "id": 500,
        "title": "Meghan Markle shares new video of Archie and Lilibet",
        "url": "https://www.express.co.uk/news/royal/2256319/meghan-markle-new-video-archie-lilibet",
        "source": "Express.co.uk",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Celebrities & Pop Culture",  # Corrected from Gaming per Phase C
        "subcategory_id": 5,
        "published_at": "2026-10-11T14:36:00Z",
        "doc_id": "18qH0cRqE4zN3x6sdHwgURi-P_L5_R4upa0paCRLussI",
        "doc_title": "ESTD - Meghan Markle Shares New Video of Archie and Lilibet Enjoying British Countryside",
        "sub_folder_id": "1P8T3mU45xGk5j4cI2aI2g92P8-v725A-"
    },
    {
        "id": 501,
        "title": "Pete Wicks sets the record straight on wedding bells with Olivia Attwood",
        "url": "https://www.mirror.co.uk/3am/celebrity-news/pete-wicks-sets-record-straight-37760211",
        "source": "Daily Mirror",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Celebrities & Pop Culture",  # Corrected from Awards per Phase C
        "subcategory_id": 5,
        "published_at": "2026-10-11T17:08:00Z",
        "doc_id": "1HSR4BIlLj6vPI7Fr8H7NtMljYezkPdlq5VSep__HXmo",
        "doc_title": "ESTD - Pete Wicks Addresses Olivia Attwood Wedding Speculation Amidst Podcast Banter",
        "sub_folder_id": "1P8T3mU45xGk5j4cI2aI2g92P8-v725A-"
    },
    {
        "id": 503,
        "title": "4 years after death, Sidhu Moosewala's hologram show debuts in Canada; song nears 900 million views on YouTube",
        "url": "https://www.livemint.com/news/trends/4-years-after-death-sidhu-moosewalas-hologram-show-debuts-in-canada-song-nears-900-million-views-on-youtube-11791724549785.html",
        "source": "Livemint",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Creators & Influencers",
        "subcategory_id": 4,
        "published_at": "2026-10-11T13:42:16Z",
        "doc_id": "1-Bx995BbDLhejfTYliwfLO9ZWm3CZLZoUYtCQ-K-eRw",
        "doc_title": "ESTD - Sidhu Moosewala Returns to Stage as Canadian Hologram Tour Launches",
        "sub_folder_id": "19zku9d6d_2vY5G5H0F6L8zD9e_01mQ8c"
    },
    {
        "id": 504,
        "title": "Elon Musk's mom Maye nearly turned down SI Swimsuit cover over 'wrinkles and cellulite'",
        "url": "https://www.foxnews.com/entertainment/elon-musk-mom-maye-nearly-turned-down-si-swimsuit-cover-wrinkles-cellulite",
        "source": "Fox News",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Celebrities & Pop Culture",  # Corrected from Digital Storytelling per Phase C
        "subcategory_id": 5,
        "published_at": "2026-10-11T13:00:19Z",
        "doc_id": "1oWhjBkmaCXbDOH4VwPW0Ae5R2XjYxKNNn2nAIdpGaos",
        "doc_title": "ESTD - Maye Musk Nearly Declined Historic SI Swimsuit Cover Over Body Image Concerns",
        "sub_folder_id": "1P8T3mU45xGk5j4cI2aI2g92P8-v725A-"
    },
    {
        "id": 509,
        "title": "గరివిడి లక్ష్మి సెన్సార్ పూర్తి.. అక్టోబర్ 17న విడుదల! (Garividi Lakshmi CBFC UA13+)",
        "url": "https://telugu.filmibeat.com/reviews/garividi-lakshmi-review-by-censor-board-cbfc-clears-anandi-tg-vishwa-prasad-movie-with-ua13-certi-177313.html",
        "source": "Filmibeat Telugu",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Movies & Cinema",
        "subcategory_id": 1,
        "published_at": "2026-10-13T04:24:25Z",
        "doc_id": "1PAb8AHJtHK-PMqJu9AJV2FSD6lrcoYSyjLi9ZcOK5qw",
        "doc_title": "ESTD - Garividi Lakshmi Secures UA13+ Certification from CBFC, Set for October 17 Release",
        "sub_folder_id": "1p6F-TR9-ALCY3H2-m71Psmq-n2kG-f-J"
    },
    {
        "id": 512,
        "title": "నేను రిలేషన్‌షిప్‌లో ఉన్నా.. రోజంతా చాటింగ్: శోభిత ధూళిపాళ (Sobhita Dhulipala ChatGPT)",
        "url": "https://telugu.filmibeat.com/heroine/sobhita-dhulipala-confesses-relationship-with-chatgpt-after-marriage-with-naga-chaitanya-177307.html",
        "source": "Filmibeat Telugu",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Celebrities & Pop Culture",
        "subcategory_id": 5,
        "published_at": "2026-10-13T04:20:10Z",
        "doc_id": "15jSqvAm2Bjsfgf9JdROVfMgOOH_GOeJNcelpt1TVM-M",
        "doc_title": "ESTD - Sobhita Dhulipala Humourously Confesses 'Relationship' with ChatGPT, Sparks Fan Relief",
        "sub_folder_id": "1P8T3mU45xGk5j4cI2aI2g92P8-v725A-"
    },
    {
        "id": 553,
        "title": "KRAFTON India Doubles College Campus Tour to 256 Colleges, Taking Competitive Esports Across India",
        "url": "https://www.tribuneindia.com/news/business/krafton-india-doubles-college-campus-tour-to-256-colleges-taking-competitive-esports-to-more-campuses-across-india-2-2/",
        "source": "The Tribune",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Gaming & Digital Entertainment",
        "subcategory_id": 6,
        "published_at": "2026-10-13T04:30:00Z",
        "doc_id": "1dHMNrH7d5tbMpYeBZKFdeuJhcEBxLthpF9eAp-jsOI4",
        "doc_title": "ESTD - KRAFTON India Doubles Esports College Tour to 256 Campuses, Expanding Competitive Gaming Reach Across India",
        "sub_folder_id": "1zN65z-E9f-Gj_U3aB_zY-2m6V5tA-9D_"
    },
    {
        "id": 557,
        "title": "‘Many of today’s top animators were my students’: Animator Nina Sabnani",
        "url": "https://www.newindianexpress.com/states/kerala/2026/Oct/12/many-of-todays-top-animators-were-my-students-says-animator-nina-sabnani",
        "source": "The New Indian Express",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Digital Storytelling & Culture",
        "subcategory_id": 8,
        "published_at": "2026-10-12T07:15:00Z",
        "doc_id": "14WFKodQq6da3DmEfMyPsc2P6GqNk0AeI2xLhpohOw14",
        "doc_title": "ESTD - Pioneering Animator Nina Sabnani Honored with IDSFFK Lifetime Achievement Award, Reflects on Indian Animation's Evolution and Cultural Storytelling",
        "sub_folder_id": "15q8o1_L-5A4P6xX8F1G7d_0zX4kL9wV8"
    },
    {
        "id": 559,
        "title": "Jailer 2 Hindi Release Row: Why PVR Inox, Cinepolis May Skip Rajinikanth's Film Over OTT Window",
        "url": "https://www.newsx.com/entertainment/jailer-2-hindi-release-row-why-pvr-inox-cinepolis-may-skip-rajinikanths-film-over-ott-window-282584/",
        "source": "NewsX",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "TV & OTT",
        "subcategory_id": 3,
        "published_at": "2026-10-13T04:15:00Z",
        "doc_id": "1akWVMOr2-j4neWahJ9-ZSvFSk3I6F8woYrkFhXbSCEU",
        "doc_title": "ESTD - Jailer 2 Hindi Release Confirmed Amidst Multiplex OTT Window Dispute",
        "sub_folder_id": "1HWXIXZI29cTXmXXx8ZN_d_F78bV8bLw_"
    },
    {
        "id": 560,
        "title": "Sidhu Moosewala's Brother Chhota Sidhu Breaks The Internet With Iconic 'Thaapi' Pose At Toronto Hologram Concert",
        "url": "https://www.timesnownews.com/entertainment-news/bollywood/sidhu-moosewala-brother-chhota-sidhu-breaks-the-internet-with-iconic-thaapi-pose-at-toronto-hologram-concert-watch-article-156324483",
        "source": "Times Now",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Music",
        "subcategory_id": 2,
        "published_at": "2026-10-13T04:10:00Z",
        "doc_id": "1y1zcThYmFiJCoi0vm1pH7r2RVLPGWLm5qOwWQ3_fBYQ",
        "doc_title": "ESTD - Chhota Sidhu Recreates Iconic 'Thaapi' at Toronto Hologram Concert, Honoring Sidhu Moosewala's Legacy",
        "sub_folder_id": "1bq69bTTu12-5UqPOyuZLkh88y5Uq0A2F"
    },
    {
        "id": 561,
        "title": "GK Group Wins Seven Prestigious Honours At FADA Dealer Awards 2026",
        "url": "https://www.devdiscourse.com/article/business/3990987-gk-group-wins-seven-prestigious-honours-at-fada-dealer-awards-2026",
        "source": "Devdiscourse",
        "category": "Business & Finance",  # Corrected to Business & Finance per Phase C
        "category_id": 3,
        "subcategory": "Trade, Supply Chain & Industry",  # Corrected to Trade & Industry
        "subcategory_id": 37,
        "published_at": "2026-10-13T04:05:00Z",
        "doc_id": "1UMXX07YBhEcNzqlpqe2bQw7kmlSaDP6aXpNDYtbKOF8",
        "doc_title": "ESTD - GK Group Secures Seven Prestigious Honours at FADA Dealer Awards 2026",
        "sub_folder_id": "1ZjbdggJuLCR9N_G-s79L2m4y_8D41V8e"
    },
    {
        "id": 562,
        "title": "Indian Social Worker Rahul Gupta Supports Emerging Content Creators: Essential Equipments Distributed",
        "url": "https://www.tribuneindia.com/news/business/indian-social-worker-rahul-gupta-supports-emerging-content-creators-essential-equipments-distributed-at-influencer-giveaway-event/",
        "source": "The Tribune",
        "category": "Entertainment",
        "category_id": 2,
        "subcategory": "Creators & Influencers",
        "subcategory_id": 4,
        "published_at": "2026-10-13T04:00:00Z",
        "doc_id": "1hRbRvPhfZMEKOART8iC1IcnBm8dXwxlKcdLfnjM2KO8",
        "doc_title": "ESTD - Rahul Gupta Initiative Empowers Emerging Indian Content Creators with Essential Equipment and Networking Opportunities",
        "sub_folder_id": "19zku9d6d_2vY5G5H0F6L8zD9e_01mQ8c"
    },
]

async def restore_and_correct():
    extractor = ExtractionService()
    cleaner = ContentCleaningService()
    
    print("Beginning restoration of 16 articles with classification corrections...")
    
    with get_db_session() as session:
        for a in ARTICLES_DATA:
            aid = a["id"]
            url = a["url"]
            print(f"\nProcessing Article {aid}: {a['title'][:60]}...")
            
            # Extract content live or fallback to existing text
            item = NewsItem(
                title=a["title"],
                url=url,
                source_name=a["source"],
                source_type="rss",
                category=a["category"],
            )
            ext = await extractor.extract_article(item, force_fetch=True)
            cln = cleaner.clean_article(ext)
            
            content = cln.cleaned_content or a["title"] * 5
            norm_url = normalize_url(url)
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            pub_at = datetime.fromisoformat(a["published_at"].replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            
            # 1. Clear existing conflicts for this specific article
            session.execute(text("DELETE FROM news_articles WHERE id = :id OR normalized_url = :norm_url OR content_hash = :hash;"), {
                "id": aid, "norm_url": norm_url, "hash": content_hash
            })
            
            # 2. Insert into news_articles
            sql_art = text("""
                INSERT INTO news_articles (
                    id, title, description, content, url, normalized_url, content_hash,
                    source_name, source_type, author, published_at, category, category_id,
                    subcategory, subcategory_id, collected_at, created_at, updated_at
                ) VALUES (
                    :id, :title, :desc, :content, :url, :norm_url, :hash,
                    :source, :stype, :author, :pub_at, :cat, :cat_id,
                    :subcat, :subcat_id, :now, :now, :now
                );
            """)
            session.execute(sql_art, {
                "id": aid,
                "title": a["title"],
                "desc": cln.description or a["title"],
                "content": content,
                "url": url,
                "norm_url": norm_url,
                "hash": content_hash,
                "source": a["source"],
                "stype": "rss",
                "author": cln.author or a["source"],
                "pub_at": pub_at,
                "cat": a["category"],
                "cat_id": a["category_id"],
                "subcat": a["subcategory"],
                "subcat_id": a["subcategory_id"],
                "now": now_dt,
            })
            
            # 3. Clear existing duplicate record and insert
            session.execute(text("DELETE FROM estd_duplicate_index WHERE article_id = :aid_str OR normalized_url = :norm_url;"), {
                "aid_str": str(aid), "norm_url": norm_url
            })
            
            sql_dup = text("""
                INSERT INTO estd_duplicate_index (
                    article_id, title, url, normalized_url, content_hash, category, subcategory,
                    source_name, source_type, author, published_at, cleaned_content, is_duplicate, created_at
                ) VALUES (
                    :aid_str, :title, :url, :norm_url, :hash, :cat, :subcat,
                    :source, :stype, :author, :pub_at_str, :cleaned, false, :now
                );
            """)
            session.execute(sql_dup, {
                "aid_str": str(aid),
                "title": a["title"],
                "url": url,
                "norm_url": norm_url,
                "hash": content_hash,
                "cat": a["category"],
                "subcat": a["subcategory"],
                "source": a["source"],
                "stype": "rss",
                "author": cln.author or a["source"],
                "pub_at_str": a["published_at"],
                "cleaned": content[:1000],
                "now": now_dt,
            })
            
            # 4. Clear existing document record and insert
            doc_id = a["doc_id"]
            doc_title = a["doc_title"]
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit?usp=drivesdk"
            
            session.execute(text("DELETE FROM google_document_records WHERE article_id = :aid OR google_document_id = :gdoc_id;"), {
                "aid": aid, "gdoc_id": doc_id
            })
            
            sql_doc = text("""
                INSERT INTO google_document_records (
                    article_id, google_document_id, google_document_url,
                    google_drive_root_folder_id, google_drive_category_folder_id,
                    google_drive_subcategory_folder_id, category, subcategory,
                    document_title, status, attempt_count, created_at, updated_at, completed_at
                ) VALUES (
                    :aid, :gdoc_id, :gdoc_url,
                    '1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8', '11n2_y1Vv6bA3m-n_H7bV9kL8p',
                    :subfolder_id, :cat, :subcat,
                    :dtitle, 'CREATED', 1, :now, :now, :now
                );
            """)
            session.execute(sql_doc, {
                "aid": aid,
                "gdoc_id": doc_id,
                "gdoc_url": doc_url,
                "subfolder_id": a["sub_folder_id"],
                "cat": a["category"],
                "subcat": a["subcategory"],
                "dtitle": doc_title,
                "now": now_dt,
            })
            
        session.commit()
        print("\nAll 16 articles committed and synchronized successfully.")

    # Read back check
    with get_db_session() as session:
        rows = session.execute(text("""
            SELECT id, title, category, category_id, subcategory, subcategory_id
            FROM news_articles
            WHERE id IN (495, 496, 497, 498, 500, 501, 503, 504, 509, 512, 553, 557, 559, 560, 561, 562)
            ORDER BY id;
        """)).fetchall()
        print(f"\n--- READ-BACK VERIFICATION ({len(rows)} articles in DB) ---")
        for r in rows:
            print(f"ID {r[0]:3d} | Cat: {r[2]} ({r[3]}) | Sub: {r[4]} ({r[5]}) | Title: {r[1][:45]}")

if __name__ == "__main__":
    asyncio.run(restore_and_correct())
