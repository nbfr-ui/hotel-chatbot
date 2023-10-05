$(document).ready(() => {
    var element = $('.floating-chat');

    const sessionId = Math.random().toString()

    element.addClass('enter');

    msgHistory = []

    function openElement() {
        var messages = element.find('.messages');
        var textInput = element.find('.text-box');
        textInput.keypress(function(event) {
            if (event.key === "Enter") {
                event.stopPropagation()
                sendNewMessage()
                return false;
            }
            return true;
        });
        element.addClass('expand');
        element.find('.chat').addClass('enter');
        textInput.keydown(onMetaAndEnter).prop("disabled", false).focus();
        element.off('click', openElement);
        element.find('#sendMessage').click(sendNewMessage);
        messages.scrollTop(messages.prop("scrollHeight"));
    }

    function lengthOf(messages) {
        return messages.map(m => m.content).join('').length
    }

    async function respond(message) {
        var messagesContainer = $('.messages');
        messagesContainer.append([
            '<li class="other animate-flicker">',
                '<span class="animate-flicker">...</span>',
            '</li>'
        ].join(''));

        try {
            msgHistory.push({ role: 'user', content: message })
            while(lengthOf(msgHistory) > 3000) {
                msgHistory = msgHistory.slice(1)
            }
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text: message, sessionId })
            })
            const answer = await response.json()
            msgHistory.push({ role: 'assistant', content: answer.text })
            if (answer.flag === 'booking_finished') {
              $('#sendMessage').text('Restart')
              $('#sendMessage').click(() => window.location.reload())
            }
            $('.messages').children().last()[0].innerHTML = `<span>${answer.text.replace(/\n/g, '<br/>')}</span>`

            return answer.flag === 'booking_finished'
        } catch (e) {
            msgHistory.push({ role: 'assistant', content: answer.text })
            $('.messages').children().last()[0].innerHTML = 'An error occurred generating the response.'
        }
        messagesContainer.finish().animate({
            scrollTop: messagesContainer.prop("scrollHeight")
        }, 250);
    }

    async function sendNewMessage() {
        var userInput = $('.text-box');
        var newMessage = userInput[0].value;

        if (!newMessage) return;

        userInput.prop("disabled", true);

        var messagesContainer = $('.messages');

        messagesContainer.append([
            '<li class="self">',
            newMessage,
            '</li>'
        ].join(''));

        userInput[0].value = '';

        messagesContainer.finish().animate({
            scrollTop: messagesContainer.prop("scrollHeight")
        }, 250);

        const finished = await respond(newMessage)
        if (!finished) {
          userInput.prop("disabled", false);
          userInput.focus();
        }

        messagesContainer.finish().animate({
            scrollTop: messagesContainer.prop("scrollHeight")
        }, 250);
    }

    function onMetaAndEnter(event) {
        if ((event.metaKey || event.ctrlKey) && event.keyCode == 13) {
            sendNewMessage();
        }
    }

    openElement()

})
