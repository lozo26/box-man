var box_man = {};
box_man.menuSetup = function () {
    $(".nav li a").click(function(e) {
        // prevent from going to the page
        e.preventDefault();

        // Fix the menu stuff
        $('.nav li.active').removeClass("active"); // Remove current active
        $(this).parent().addClass("active") // make this li active

        // Load the results table based on the url
        var href = $(this).attr("href");
        $("#results").load(href + " #results", function () {
            // Setup the cascading drop downs if they've just been loaded
            box_man.dropDownSetup();
        });
        $(".jumbotron").load(href + " #title");

    });

    // Make sure the admin menu doesn't do the load
    $("#admin-menu li a").unbind("click")
}

box_man.dropDownSetup = function () {
    $('#level').change(function(){
        // Remove existing options first
        $('#athletes').empty();

        // Call ajax to get athlete names and populate dropdown
        var sel = $('#level').find(":selected").text();
        $.getJSON( '/athlete', {level: sel})
        .done(function( data ) {
            $.each(data , function(i, v) {
                console.log("i: " + i + " v.name: " + v.name);
                $('#athletes').append(new Option(v.name, v.name))
            });
        });
    });
}

// TODO: Add code to make the x-editable controls for admins
box_man.adminFormSetup = function () {
    //toggle `popup` / `inline` mode
    $.fn.editable.defaults.mode = 'popup';     
    
    //make username editable
    $('#username').editable();
    
    //make status editable
    $('#status').editable({
        type: 'select',
        title: 'Select status',
        placement: 'right',
        value: 2,
        source: [
            {value: 1, text: 'status 1'},
            {value: 2, text: 'status 2'},
            {value: 3, text: 'status 3'}
        ]
        /*
        //uncomment these lines to send data on server
        ,pk: 1
        ,url: '/post'
        */
    });
}


$(document).ready(function() {
    box_man.menuSetup();
});



