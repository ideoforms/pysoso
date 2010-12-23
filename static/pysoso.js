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

	$('html').keypress(function(event)
	{
		if (event.target.tagName == "INPUT")
			return;

  		if (event.which == 99)
			$('#controls .bookmarks_show').click();
  		if (event.which == 101)
			$('a#edit').click();
		// else if (event.which = 110)
		else if (event.which == 115)
			$('#bookmarks_stale .bookmarks_show').click();
	});

	$('a#edit').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			$(this).removeClass("active");
			$("#bookmarks .tools").hide();
		}
		else
		{
			$(this).addClass("active");
			$("#bookmarks .tools").show();
		}
		return false;
	});

	$('.tag_show').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			var li = $(this).parents("#bookmarks").find("li");
			li.show();
			$(this).removeClass("active");
		}
		else
		{
			var tag = $(this).attr("title");
			var li = $(this).parents("#bookmarks").find("li[tags~=" + tag + "]");
			li.show();
			li = $(this).parents("#bookmarks").find("li:not([tags~=" + tag + "])");
			li.hide();
			$(this).parents("h2").find(".tag_show").removeClass("active");
			$(this).addClass("active");
		}
	});

	$('.bookmarks_show').bind('click', function () {
		var ul = $(this).parents("div").children("ul");
		if (ul.is(":visible"))
		{
			ul.hide("fast");
			$(this).removeClass("active");
		}
		else
		{
			ul.show("fast");
			$(this).addClass("active");
		}

		return false;
	});

	$('#bookmarks .edit').bind('mouseover', function () {
		var el = $(this).parents("li").find(".link");
		el[0].style.textDecoration = "underline";
	});

	$('#bookmarks .edit').bind('mouseout', function () {
		var el = $(this).parents("li").find(".link");
		el[0].style.textDecoration = "none";
	});

	$('#bookmarks .delete').bind('mouseover', function () {
		var el = $(this).parents("li").find(".link");
		el[0].style.textDecoration = "line-through";
	});

	$('#bookmarks .delete').bind('mouseout', function () {
		var el = $(this).parents("li").find(".link");
		el[0].style.textDecoration = "none";
	});


	$('#bookmarks .delete').bind('click', function () {
		$(this).parents("li").hide("fast");
		$.getJSON($(this).attr("href"));
		return false;
	});

	$('#bookmarks .bookmark').bind('click', function () {
		$(this).parents("li").hide("fast", function () { $(this).remove(); });
	});


});
