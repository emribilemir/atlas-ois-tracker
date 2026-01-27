"""
Telegram bot with monitoring commands and inline keyboard buttons.
"""
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from .config import Config
from .ois_scraper import OISScraper
from .grade_storage import GradeStorage, format_changes, format_full_grades


def get_keyboard(monitoring: bool = False):
    """Get inline keyboard with command buttons."""
    if monitoring:
        buttons = [
            [
                InlineKeyboardButton("🛑 Durdur", callback_data="stop"),
                InlineKeyboardButton("📊 Durum", callback_data="status"),
            ],
            [
                InlineKeyboardButton("🔍 Kontrol Et", callback_data="check"),
            ]
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton("▶️ Başlat", callback_data="start"),
                InlineKeyboardButton("📊 Durum", callback_data="status"),
            ],
            [
                InlineKeyboardButton("🔍 Kontrol Et", callback_data="check"),
            ]
        ]
    return InlineKeyboardMarkup(buttons)


class GradeCheckerBot:
    """Telegram bot for grade checking."""
    
    def __init__(self):
        self.scraper = OISScraper()
        self.storage = GradeStorage()
        self.monitoring = False
        self.last_check: datetime | None = None
        self.check_count = 0
        self.app: Application | None = None
        self._monitor_task: asyncio.Task | None = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - start monitoring."""
        if self.monitoring:
            await update.message.reply_text(
                "⚠️ Monitoring zaten aktif!",
                reply_markup=get_keyboard(self.monitoring)
            )
            return
        
        self.monitoring = True
        await update.message.reply_text(
            "✅ *Monitoring başlatıldı!*\n\n"
            f"⏰ Kontrol aralığı: {Config.CHECK_INTERVAL // 60} dakika",
            parse_mode="Markdown",
            reply_markup=get_keyboard(self.monitoring)
        )
        
        # Start the monitoring loop
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command - stop monitoring."""
        if not self.monitoring:
            await update.message.reply_text(
                "⚠️ Monitoring zaten kapalı!",
                reply_markup=get_keyboard(self.monitoring)
            )
            return
        
        self.monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        
        # Close browser
        await self.scraper.close()
        
        await update.message.reply_text(
            "🛑 *Monitoring durduruldu.*",
            parse_mode="Markdown",
            reply_markup=get_keyboard(self.monitoring)
        )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - show current status."""
        status_emoji = "🟢" if self.monitoring else "🔴"
        status_text = "Aktif" if self.monitoring else "Kapalı"
        
        last_check_text = "Henüz kontrol yapılmadı"
        if self.last_check:
            last_check_text = self.last_check.strftime("%d/%m/%Y %H:%M:%S")
        
        summary = self.storage.get_summary()
        
        await update.message.reply_text(
            f"{status_emoji} *Monitoring Durumu:* {status_text}\n\n"
            f"🕐 Son kontrol: {last_check_text}\n"
            f"🔄 Toplam kontrol: {self.check_count}\n"
            f"⏰ Aralık: {Config.CHECK_INTERVAL // 60} dakika\n\n"
            f"{summary}",
            parse_mode="Markdown",
            reply_markup=get_keyboard(self.monitoring)
        )
    
    async def check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command - force immediate check."""
        await update.message.reply_text("🔍 Notlar kontrol ediliyor...")
        
        try:
            result = await self._perform_check()
            
            if result is None:
                await update.message.reply_text(
                    "❌ *Giriş başarısız!*\n"
                    "CAPTCHA çözülemedi veya bilgiler hatalı olabilir.",
                    parse_mode="Markdown",
                    reply_markup=get_keyboard(self.monitoring)
                )
                return
            
            changes, grades = result
            
            # Update storage (changes are already returned by compare_and_update, 
            # but we want to show full list regardless of changes for manual check)
            
            full_list = format_full_grades(grades)
            await update.message.reply_text(
                f"{full_list}",
                parse_mode="Markdown",
                reply_markup=get_keyboard(self.monitoring)
            )
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ Hata: {e}",
                reply_markup=get_keyboard(self.monitoring)
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button presses."""
        query = update.callback_query
        await query.answer()
        
        # Create a fake update with message for reusing command handlers
        if query.data == "start":
            if self.monitoring:
                await query.edit_message_text(
                    "⚠️ Monitoring zaten aktif!",
                    reply_markup=get_keyboard(self.monitoring)
                )
                return
            
            self.monitoring = True
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            await query.edit_message_text(
                f"✅ *Monitoring başlatıldı!*\n\n"
                f"⏰ Kontrol aralığı: {Config.CHECK_INTERVAL // 60} dakika",
                parse_mode="Markdown",
                reply_markup=get_keyboard(self.monitoring)
            )
        
        elif query.data == "stop":
            if not self.monitoring:
                await query.edit_message_text(
                    "⚠️ Monitoring zaten kapalı!",
                    reply_markup=get_keyboard(self.monitoring)
                )
                return
            
            self.monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                self._monitor_task = None
            await self.scraper.close()
            
            await query.edit_message_text(
                "🛑 *Monitoring durduruldu.*",
                parse_mode="Markdown",
                reply_markup=get_keyboard(self.monitoring)
            )
        
        elif query.data == "status":
            status_emoji = "🟢" if self.monitoring else "🔴"
            status_text = "Aktif" if self.monitoring else "Kapalı"
            
            last_check_text = "Henüz kontrol yapılmadı"
            if self.last_check:
                last_check_text = self.last_check.strftime("%d/%m/%Y %H:%M:%S")
            
            summary = self.storage.get_summary()
            
            await query.edit_message_text(
                f"{status_emoji} *Monitoring Durumu:* {status_text}\n\n"
                f"🕐 Son kontrol: {last_check_text}\n"
                f"🔄 Toplam kontrol: {self.check_count}\n"
                f"⏰ Aralık: {Config.CHECK_INTERVAL // 60} dakika\n\n"
                f"{summary}",
                parse_mode="Markdown",
                reply_markup=get_keyboard(self.monitoring)
            )
        
        elif query.data == "check":
            await query.edit_message_text("🔍 Notlar kontrol ediliyor...")
            
            try:
                result = await self._perform_check()
                
                if result is None:
                    await query.edit_message_text(
                        "❌ *Giriş başarısız!*\n"
                        "CAPTCHA çözülemedi veya bilgiler hatalı olabilir.",
                        parse_mode="Markdown",
                        reply_markup=get_keyboard(self.monitoring)
                    )
                    return
                
                changes, grades = result
                
                full_list = format_full_grades(grades)
                await query.edit_message_text(
                    f"{full_list}",
                    parse_mode="Markdown",
                    reply_markup=get_keyboard(self.monitoring)
                )
                    
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Hata: {e}",
                    reply_markup=get_keyboard(self.monitoring)
                )
    
    async def _perform_check(self) -> tuple[list, dict] | None:
        """Perform a grade check. Returns (changes, grades) or None if failed."""
        grades = await self.scraper.fetch_grades()
        
        if grades is None:
            return None
        
        self.last_check = datetime.now()
        self.check_count += 1
        
        changes = self.storage.compare_and_update(grades)
        
        return changes, grades
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                result = await self._perform_check()
                
                if result:
                    changes, _ = result
                    if changes:
                        await self.app.bot.send_message(
                            chat_id=Config.TELEGRAM_CHAT_ID,
                            text=format_changes(changes),
                            parse_mode="Markdown",
                            reply_markup=get_keyboard(self.monitoring)
                        )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
            
            await asyncio.sleep(Config.CHECK_INTERVAL)
    
    def run(self):
        """Run the bot."""
        missing = Config.validate()
        if missing:
            print(f"❌ Missing environment variables: {', '.join(missing)}")
            print("Please check your .env file!")
            return
        
        self.app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("stop", self.stop))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("check", self.check))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        print("🤖 Bot starting...")
        print(f"📱 Chat ID: {Config.TELEGRAM_CHAT_ID}")
        print(f"⏰ Check interval: {Config.CHECK_INTERVAL}s")
        
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
