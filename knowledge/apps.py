from django.apps import AppConfig
import os

class KnowledgeConfig(AppConfig):
    name = 'knowledge'

    def ready(self):
        from django.core.management import call_command
        from .management.commands.DTA_init import Command
        import knowledge.signals  # 导入信号模块
        
        command = Command()
        command.handle()
        
        print("KnowledgeConfig.ready() is being executed")

        # 检查 Redis 是否已加载数据，避免重复加载
        if os.getenv('RUN_MAIN', None) != 'true':  # 避免开发服务器重复加载
            try:
                call_command('load_medical_data')
            except Exception as e:
                print(f"Failed to load medical data: {e}")