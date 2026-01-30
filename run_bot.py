#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт запуска бота с проверками
Использование: python run_bot.py
"""
import os
import sys
from pathlib import Path

def setup_environment():
    """Настройка переменных окружения по умолчанию"""
    # Устанавливаем значения по умолчанию если не заданы
    defaults = {
        'BOT_TOKEN': '',
        'DB_PATH': 'bot.db',
        'ADMIN_IDS': '',
        'LOG_LEVEL': 'INFO',
        'GAMIFICATION_ENABLED': 'true',
        'AUTO_MODERATION': 'true',
        'USE_AI_RECOMMENDATIONS': 'false',
    }
    
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value

def check_token():
    """Проверка наличия токена"""
    token = os.environ.get('BOT_TOKEN', '')
    
    if not token or token == 'YOUR_BOT_TOKEN_HERE':
        print("\n" + "="*70)
        print("❌ ОШИБКА: Токен бота не настроен!")
        print("="*70)
        print("\n📝 Как получить токен:")
        print("   1. Откройте Telegram и найдите @BotFather")
        print("   2. Отправьте команду: /newbot")
        print("   3. Следуйте инструкциям и выберите имя для бота")
        print("   4. Скопируйте полученный токен (примерно так: 123456789:ABCdefGHI...)")
        print("\n⚙️ Как установить токен:")
        print("\n   Linux/Mac:")
        print("   export BOT_TOKEN='ваш_токен_здесь'")
        print("   python run_bot.py")
        print("\n   Windows (CMD):")
        print("   set BOT_TOKEN=ваш_токен_здесь")
        print("   python run_bot.py")
        print("\n   Windows (PowerShell):")
        print("   $env:BOT_TOKEN='ваш_токен_здесь'")
        print("   python run_bot.py")
        print("\n" + "="*70 + "\n")
        return False
    
    return True

def check_dependencies():
    """Проверка необходимых зависимостей"""
    required = ['aiogram', 'aiosqlite', 'pydantic', 'pydantic_settings']
    missing = []
    
    print("🔍 Проверка зависимостей...")
    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"   ❌ {package}")
    
    if missing:
        print(f"\n❌ Отсутствуют зависимости: {', '.join(missing)}")
        print("📦 Установите их командой:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    """Главная функция"""
    print("🚀 Запуск SwapBot...\n")
    
    # Настройка окружения
    setup_environment()
    
    # Проверка токена
    if not check_token():
        sys.exit(1)
    
    # Проверка зависимостей
    if not check_dependencies():
        sys.exit(1)
    
    # Запуск бота
    print("\n✅ Все проверки пройдены!")
    print("🤖 Запуск бота...\n")
    print("="*70)
    
    try:
        import asyncio
        from app.bot import main as bot_main
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен пользователем")
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("Убедитесь что структура проекта правильная")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
