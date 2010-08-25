/*
 * Dashboard for Comet Tail
 */

function create_watch_window(title, filename)
{
    var dialog = $('#filewatch_win').dialog({ 
            width : 200, heigth: 400});
    $('#filewatch_windows').append(dialog);
}

$(document).ready(function() {
    $('#addfile').click(
	function() {
	    $('#dialog').dialog({
		buttons : {"Watch" : function() {
		    create_watch_window($('#title').attr('value'),
					$('#filename').attr('value'));
		}}});
	});
});

$(function() {
    $('<input type="button" id="toggleButton" value="Hide">').insertBefore('#disclaimer');
    $('#toggleButton').click(function() {
	$('#disclaimer').toggle('fast', function () {
	    if ($('#disclaimer').is(':visible')) {
		$('#toggleButton').val('Hide');
	    } else {
		$('#toggleButton').val('Show');
	    }
	});
    })
});
 

$(function() {
    $('<input type="button" id="animateButton" value="Animate">').insertBefore('#disclaimer');
    $('#animateButton').click(function() {
	$('#disclaimer').animate({ 
	    'backgroundColor':'#ff9f5f'}, 2000
				);
    })
});
