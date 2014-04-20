var box_man = {};

box_man.load = function(anchor) {
    // Load the results table based on the url
    var href = $(anchor).attr("href");
    $("#content").load(href + " #results");
    $(".jumbotron").load(href + " #title");
}

box_man.menuSetup = function () {
    $(".nav li a").click(function(e) {
        // prevent from going to the page
        e.preventDefault();

        // Fix the menu stuff
        $('.nav li.active').removeClass("active");  // Remove current active
        $(this).parent().addClass("active");        // make this li active

        box_man.load(this);
    });

    // Make sure the admin menu doesn't do the load
    $("#admin-menu li a").unbind("click")
}

box_man.btnSetup = function() {
    $("#content").on("click", "a.btn",  function(e){
        // prevent from going to the page
        e.preventDefault();

        box_man.load(this);
    });
}

box_man.submitBtnSetup = function() {
    //callback handler for form submit
    $("#content").on("submit", "form.ajax-form", function(e) {
        e.preventDefault(); //STOP default action

        var postData = $(this).serializeArray();
        var formURL = $(this).attr("action");
        $.post(
            formURL, 
            postData, 
            function(data, textStatus, jqXHR) {
                var nodes = $.parseHTML(data)
                $.each(nodes, function(idx, el) {
                    // finds <h1 id='title'>...</h1>
                    if ($(el).attr('id') === 'title') {
                        $(".jumbotron").html(el);
                    }

                    // finds <div id='results'>...</div>
                    if ($(el).attr('id') === 'results') {
                        $("#content").html(el);
                    }
                });
            });
    });
}

box_man.addWoddBtnSetup = function() {
    $("#content").on("click", "#add-wod", function(e) {
        e.preventDefault();
        // TODO: How do I _easily_ get this from the server instead of hard-coding it here
        var new_wod_input = (
          '<div class="form-inline" style="margin-top: 5px;">' +
          '   <div class="form-group">' +
          '       <label class="sr-only" for="wodname">Wod Name</label>' + 
          '       <input type="text" class="form-control" name="wodname" placeholder="Wod Name" />' +
          '   </div>' +
          '   <div class="form-group">' +
          '       <label class="sr-only" for="maxPoints">Max Points</label>' +
          '       <input type="text" class="form-control" name="maxPoints" placeholder="Max Points" />' +
          '   </div>' +
          '   <div class="form-group">' +
          '       <label class="sr-only" for="pointInterval">Point Interval</label>' +
          '       <input type="text" class="form-control" name="pointInterval" placeholder="Point Interval" />' +
          '   </div>' +
          '</div>')
        $("#wods").append($(new_wod_input).fadeIn('slow'));
    });
}

box_man.scoresSetup = function() {
    $('#content').on("change",  "#div-sel", function() {
        console.log('get scores for ' + $(this).find(":selected").text());
        var url = $(this).val();
        if (url === "") return false; // ignore default

        $.get(url, function( data ) {
            $( "#score-table" ).html( data );
            console.log("Scores were loaded");
        });
    });
}

box_man.scoreTableSetup = function () {
    //toggle `popup` / `inline` mode
    $.fn.editable.defaults.mode = 'inline';     
    
    //make cells editable
    $('#content').editable({
        selector: 'a.editable-score',
        url: '/admin/edit/score',
        showbuttons: false,
    });
}


$(document).ready(function() {
    box_man.menuSetup();
    box_man.btnSetup();
    box_man.addWoddBtnSetup();
    box_man.submitBtnSetup();
    box_man.scoresSetup();
    box_man.scoreTableSetup();
});



