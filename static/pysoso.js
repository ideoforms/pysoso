$SCRIPT_ROOT = "/pysoso";


$(function()
{
	$('a#calculate').bind('click', function() {
		$.getJSON($SCRIPT_ROOT + '/_add_numbers', {
			a: $('input[name="a"]').val(),
			b: $('input[name="b"]').val()
		}, function(data) {
			$("#result").text(data.result);
		});
		return false;
	});

	$('a#edit').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			$(this).removeClass("active");
			$("div.bookmarks .tools").removeClass("visible");
		}
		else
		{
			$(this).addClass("active");
			$("div.bookmarks .tools").addClass("visible");
		}
		return false;
	});

	$('#bookmarks_hide').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			$(this).removeClass("active");
			$(this).text("show");
			$("#bookmarks_stale ul").addClass("folded");
		}
		else
		{
			$(this).addClass("active");
			$(this).text("hide");
			$("#bookmarks_stale ul").removeClass("folded");
		}
	});

	$('.bookmarks .delete').bind('click', function () {
		$(this).parents("li").hide("slow");
		$.getJSON($(this).attr("href"));
		return false;
	});

	$('.bookmarks .bookmark').bind('click', function () {
		$(this).parents("li").hide("slow");
	});
});
