fn is_word_char(c: char) -> bool {
    // A word is made up of letters and/or numbers.
    c.is_ascii_alphanumeric()
}

pub fn reverse_words(s: &str) -> String {
    let mut out: Vec<char> = s.chars().collect();

    let mut i = 0usize;
    while i < out.len() {
        if !is_word_char(out[i]) {
            i += 1;
            continue;
        }

        let start = i;
        while i < out.len() && is_word_char(out[i]) {
            i += 1;
        }
        let end = i; // one past last word char

        out[start..end].reverse();
    }

    out.into_iter().collect()
}

fn main() {
    let test_str = "String; 2be reversed...";
    assert_eq!(reverse_words(test_str), "gnirtS; eb2 desrever...");
}

#[cfg(test)]
mod tests {
    use super::reverse_words;

    #[test]
    fn sample() {
        assert_eq!(
            reverse_words("String; 2be reversed..."),
            "gnirtS; eb2 desrever..."
        );
    }

    #[test]
    fn additional_cases() {
        assert_eq!(reverse_words(""), "");
        assert_eq!(reverse_words("   "), "   ");
        assert_eq!(reverse_words("a"), "a");
        assert_eq!(reverse_words("ab cd"), "ba dc");
        assert_eq!(reverse_words("ab,cd"), "ba,dc");
        assert_eq!(reverse_words("A1b2 C3"), "2b1A 3C");
    }
}

