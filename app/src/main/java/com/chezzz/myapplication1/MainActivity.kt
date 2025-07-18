package com.example.wikicarousel

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.VerticalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            WikiApp()
        }
    }
}

// ------------------ Модель данных -------------------

@Serializable
data class WikiArticle(
    val title: String,
    val extract: String,
    val thumbnail: Thumbnail? = null,
    val content_urls: ContentUrls? = null
)

@Serializable
data class Thumbnail(val source: String?)
@Serializable
data class ContentUrls(val desktop: Desktop?)
@Serializable
data class Desktop(val page: String?)

// ------------------ Загрузка статьи -------------------

suspend fun fetchRandomWikiArticle(): WikiArticle? = withContext(Dispatchers.IO) {
    try {
        val client = OkHttpClient()
        val request = Request.Builder()
            .url("https://ru.wikipedia.org/api/rest_v1/page/random/summary")
            .build()
        val response = client.newCall(request).execute()
        if (response.isSuccessful) {
            response.body?.string()?.let { body ->
                val json = Json { ignoreUnknownKeys = true }
                return@withContext json.decodeFromString(WikiArticle.serializer(), body)
            }
        }
    } catch (e: Exception) {
        e.printStackTrace()
    }
    null
}

// ------------------ UI -------------------

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun WikiApp() {
    var articles by remember { mutableStateOf(listOf<WikiArticle>()) }

    // Загрузка первой статьи
    LaunchedEffect(Unit) {
        val article = fetchRandomWikiArticle()
        article?.let { articles = listOf(it) }
    }

    val pagerState = rememberPagerState(
        pageCount = { articles.size },
        initialPage = 0
    )

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(title = { Text("Wiki Carousel") })
        }
    ) { padding ->
        if (articles.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            VerticalPager(
                state = pagerState,
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
            ) { page ->
                WikiCard(article = articles[page])

                // Загружаем следующую статью на последней странице
                LaunchedEffect(page) {
                    if (page == articles.lastIndex) {
                        val next = fetchRandomWikiArticle()
                        if (next != null) {
                            articles = articles + next
                        }
                    }
                }
            }
        }
    }
}

// ------------------ Карточка статьи -------------------

@Composable
fun WikiCard(article: WikiArticle) {
    val context = LocalContext.current
    var lastTapTime by remember { mutableStateOf(0L) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(Unit) {
                detectTapGestures(
                    onTap = {
                        val now = System.currentTimeMillis()
                        if (now - lastTapTime < 300) {
                            article.content_urls?.desktop?.page?.let { url ->
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                                context.startActivity(intent)
                            }
                        }
                        lastTapTime = now
                    }
                )
            }
    ) {
        // Фоновое изображение
        article.thumbnail?.source?.let { imageUrl ->
            AsyncImage(
                model = imageUrl,
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )
        }

        // Заголовок и текст на фоне
        Column(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .background(Color.Black.copy(alpha = 0.6f))
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = article.title,
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = article.extract,
                fontSize = 16.sp,
                color = Color.White,
                maxLines = 6
            )
        }
    }
}
