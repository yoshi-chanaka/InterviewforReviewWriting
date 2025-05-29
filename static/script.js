let mode = 0; /* 0: guidance mode, 1: question mode*/

function addutterance(text) {
    return $.ajax({
        url: '/add_user_utterance',
        type: 'POST',
        data: { text: text },
        success: function (response) {
            $('.chat-history').append(response.element);
            $('#send-message').val('');
            ScrollHistory();
        },
        error: function (error) {
            console.log(error);
        }
    });
}


$(document).ready(function () {

    $('#send-button').click(addElement);

    let question_number = 0;
    let guidance_number = 0;
    const NUM_GUIDANCE = 1;
    let worker_id = ''

    let $init_textarea = $('#send-message');
    let init_lineHeight = parseInt($init_textarea.css('lineHeight'));
    $init_textarea.height(init_lineHeight);
    ControlHeight();

    $(function(){
        $('#send-message').keydown(function(e){
            if (event.ctrlKey){
                if (e.keyCode === 13) {
                    addElement();
                return false;
                }
            }
        })
    })

    async function addElement() {
        var text = $('#send-message').val();
        if (text.trim().length && mode==0) {
            // 準備
            addutterance(text).pipe(
                function () {
                    $.ajax({
                        url: '/post_guidance',
                        type: 'POST',
                        data: { text: text , q_number: guidance_number, worker_id: worker_id, num_guidance: NUM_GUIDANCE},
                        success: function (response) {
                            $('.chat-history').append(response.element);
                            $('#send-message').val('');
                            ScrollHistory();
                            guidance_number += 1;
                            if (guidance_number >= NUM_GUIDANCE) {
                                mode += 1;
                                worker_id = response.worker_id
                                AddFirstQuestion();
                                ScrollHistory();
                                question_number += 1;
                            }
                            worker_id = response.worker_id
                            // console.log(worker_id)
                        },
                        error: function (error) {
                            console.log(error);
                        }
                    })
                }
            )
        }

        else if (text.trim().length && mode==1) {
            /* ここをChatGPT用に書き換える */
            addutterance(text).pipe(
                function () {
                    $.ajax({
                        url: '/post_question',
                        type: 'POST',
                        data: { text: text , q_number: question_number, worker_id: worker_id},
                        success: function (response) {
                            if (response.end_sign) {
                                $('.chat-history').append(response.element);
                                TerminateChat();
                            }
                            else {
                                $('.chat-history').append(response.element);
                            }
                            $('#send-message').val('');
                            ScrollHistory();
                            question_number += 1;
                            // console.log(question_number)
                            // console.log(response.end_sign)
                        },
                        error: function (error) {
                            console.log(error);
                        }
                    })
                }
            )
        }
        else {
            console.log("text is not input")
        }
    }

    async function AddFirstQuestion() {
        $.ajax({
            url: '/post_question',
            type: 'POST',
            data: {q_number: question_number, worker_id: worker_id},
            success: function (response) {
                $('.chat-history').append(response.element);
                $('#send-message').val('');
                ScrollHistory();
            },
            error: function (error) {
                console.log(error);
            }
        });
    }

    function TerminateChat() {
        $.ajax({
            url: '/terminate_interview',
            type: 'POST',
            data: {worker_id: worker_id},
            success: function (response) {
                $('.chat-history').append(response.element);
                $('#send-message').val('');
                ScrollHistory();
            },
            error: function (error) {
                console.log(error);
            }
        });
    }

});

$(document).ajaxStop(function () {
    ControlHeight();

    var $textarea = $('#send-message');
    var lineHeight = parseInt($textarea.css('lineHeight'));
    var lines = ($(this).val() + '\n').match(/\n/g).length;
    $textarea.height(lineHeight * lines);

});


function ReflectReview(review) {
    $.ajax({
        url: '/interviewresult',
        type: 'GET',
        data: {review: review},
        success: function (response) {
        },
        error: function (error) {
            console.log(error);
        }
    });
}

function TextareaToPreventer () {
    var send_preventer = document.createElement("div");
    send_preventer.setAttribute("id", "send-preventer");
    send_preventer.textContent = "Wait";
    var send_button = document.getElementById("send-message");
    send_button.replaceWith(send_preventer);
}

function ControlHeight() {
    var $textarea = $('#send-message');
    var lineHeight = parseInt($textarea.css('lineHeight'));
    $textarea.on('input', function (e) {
        var lines = ($(this).val() + '\n').match(/\n/g).length;
        $(this).height(lineHeight * lines);
    });
};

async function ScrollHistory(){
    var scrollerInner = document.querySelector(".chat-history")
    scrollerInner.scrollTop += 1000;
}


window.addEventListener('beforeunload', function (e) {
    e.returnValue = 'wait';
}, false);

