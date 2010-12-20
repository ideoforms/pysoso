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
			$("#bookmarks .tools").removeClass("visible");
		}
		else
		{
			$(this).addClass("active");
			$("#bookmarks .tools").addClass("visible");
		}
		return false;
	});

	$('#bookmarks_show').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			$(this).removeClass("active");
			// $(this).text("show");
			// $("#bookmarks_stale ul").addClass("nodisplay");
			$("#bookmarks_stale ul").hide("slow");
		}
		else
		{
			$(this).addClass("active");
			// $(this).text("hide");
			// $("#bookmarks_stale ul").removeClass("nodisplay");
			$("#bookmarks_stale ul").show("slow");
		}
	});

	$('#bookmarks .edit').bind('mouseover', function () {
		var el = $(this).parents("li").children(".bookmark")[0];
		el.style.textDecoration = "underline";
	});

	$('#bookmarks .edit').bind('mouseout', function () {
		var el = $(this).parents("li").children(".bookmark")[0];
		el.style.textDecoration = "none";
	});

	$('#bookmarks .delete').bind('mouseover', function () {
		var el = $(this).parents("li").children(".bookmark")[0];
		el.style.textDecoration = "line-through";
	});

	$('#bookmarks .delete').bind('mouseout', function () {
		var el = $(this).parents("li").children(".bookmark")[0];
		el.style.textDecoration = "none";
	});


	$('#bookmarks .delete').bind('click', function () {
		$(this).parents("li").hide("slow");
		$.getJSON($(this).attr("href"));
		return false;
	});

	$('#bookmarks .bookmark').bind('click', function () {
		$(this).parents("li").hide("slow");
	});
});
