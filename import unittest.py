import unittest
from unittest.mock import patch, MagicMock
import main

# test_main.py



class TestMain(unittest.TestCase):
    @patch('main.speak')
    @patch('main.initialize_llm')
    def test_run_assistant_llm_fail(self, mock_init_llm, mock_speak):
        mock_init_llm.return_value = None
        tray_icon = MagicMock()
        main.run_assistant(tray_icon)
        mock_speak.assert_any_call("Assistant cannot start because the AI model failed to load.")

    @patch('main.speak')
    @patch('main.initialize_llm', return_value='llm')
    @patch('main.sr.Recognizer')
    @patch('main.sr.Microphone')
    @patch('main.listen_for_wake_word', return_value=False)
    def test_run_assistant_wake_word_fail(self, mock_wake, mock_mic, mock_rec, mock_init_llm, mock_speak):
        tray_icon = MagicMock()
        tray_icon.visible = True
        main.run_assistant(tray_icon)
        mock_speak.assert_any_call("Halting due to a critical microphone error.")
        tray_icon.stop.assert_called_once()

    @patch('main.speak')
    @patch('main.initialize_llm', return_value='llm')
    @patch('main.sr.Recognizer')
    @patch('main.sr.Microphone')
    @patch('main.listen_for_wake_word', return_value=True)
    @patch('main.listen_for_command', side_effect=['cmd', None])
    @patch('main.command_dispatcher', return_value=False)
    def test_run_assistant_dispatcher_exit(self, mock_dispatcher, mock_cmd, mock_wake, mock_mic, mock_rec, mock_init_llm, mock_speak):
        tray_icon = MagicMock()
        tray_icon.visible = True
        main.run_assistant(tray_icon)
        tray_icon.stop.assert_called_once()

    @patch('main.speak')
    @patch('main.initialize_llm', return_value='llm')
    @patch('main.sr.Recognizer')
    @patch('main.sr.Microphone', side_effect=IOError("Mic error"))
    def test_run_assistant_microphone_error(self, mock_mic, mock_rec, mock_init_llm, mock_speak):
        tray_icon = MagicMock()
        main.run_assistant(tray_icon)
        mock_speak.assert_any_call("Could not access the microphone. Please ensure it is connected and permissions are set.")

    @patch('main.speak')
    @patch('main.initialize_llm', return_value='llm')
    @patch('main.sr.Recognizer')
    @patch('main.sr.Microphone', side_effect=Exception("Unexpected"))
    def test_run_assistant_unexpected_error(self, mock_mic, mock_rec, mock_init_llm, mock_speak):
        tray_icon = MagicMock()
        main.run_assistant(tray_icon)
        mock_speak.assert_any_call("An unexpected error occurred with the microphone.")

    @patch('main.sys.exit')
    def test_quit_assistant(self, mock_exit):
        tray_icon = MagicMock()
        main.assistant_thread_running = True
        main.quit_assistant(tray_icon, None)
        self.assertFalse(main.assistant_thread_running)
        tray_icon.stop.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('main.threading.Thread')
    @patch('main.icon')
    @patch('main.Image.open')
    @patch('main.item')
    def test_main(self, mock_item, mock_img_open, mock_icon, mock_thread):
        mock_icon_inst = MagicMock()
        mock_icon.return_value = mock_icon_inst
        mock_img_open.return_value = MagicMock()
        mock_thread_inst = MagicMock()
        mock_thread.return_value = mock_thread_inst
        main.main()
        mock_thread.assert_called_once()
        mock_icon_inst.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()