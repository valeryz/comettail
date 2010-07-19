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
