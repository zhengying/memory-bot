


# ============================
# Edge Cases
# ============================

class TestDiscordBotEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_message(self):
        """Test handling empty message"""
        from discord_bot.commands import CommandParser
        
        parser = CommandParser(prefix="!")
        result = parser.parse("")
        
        assert result.type == "none"
    
    def test_long_message(self):
        """Test handling very long message"""
        from discord_bot.commands import CommandParser
        
        parser = CommandParser(prefix="!")
        long_content = "a" * 2000
        result = parser.parse(f"!chat {long_content}")
        
        assert result.type == "command"
        assert result.command == "chat"
    
    def test_special_characters_in_message(self):
        """Test handling special characters"""
        from discord_bot.commands import CommandParser
        
        parser = CommandParser(prefix="!")
        result = parser.parse("!chat Hello <@123> #channel !test")
        
        assert result.type == "command"
        assert "<@123>" in result.args
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test handling agent errors gracefully"""
        from discord_bot.commands import CommandHandler
        
        mock_agent = Mock()
        mock_agent.chat.side_effect = Exception("LLM API error")
        
        handler = CommandHandler(agent=mock_agent)
        result = await handler.handle_command(
            command="chat",
            args=["Hello"],
            user_id="user123"
        )
        
        assert result["success"] is False
