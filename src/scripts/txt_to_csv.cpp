#include <iostream>
#include <fstream>
#include <sstream>
#include <string_view>
#include <unordered_map>
#include <vector>
#include <filesystem>
#include <unordered_set>

constexpr size_t BATCH_SIZE = 1024 * 1024; // 1MB

std::string escape_quotes(const std::string& value) {
    std::string escaped_value;
    for (char c : value) {
        if (c == '"')
            escaped_value += "\"\"";
        else 
            escaped_value += c;
    }
    return escaped_value;
}

void write_header(std::ofstream& output_file, const std::vector<std::string>& headers) {
    for (size_t i = 0; i < headers.size(); ++i) {
        output_file << headers[i];
        if (i < headers.size() - 1) output_file << ",";
    }
    output_file << "\n";
}

void write_object(std::ostringstream& buffer, const std::vector<std::string>& headers, const std::unordered_map<std::string, std::string>& object) {
    for (size_t i = 0; i < headers.size(); ++i) {
        auto it = object.find(headers[i]);
        if (it != object.end()) {
            if (it->second.find(',') != std::string::npos || it->second.find('"') != std::string::npos)
                buffer << "\"" << std::move(escape_quotes(it->second)) << "\"";
            else
                buffer << it->second;
        }
        if (i < headers.size() - 1) buffer << ",";
    }
    buffer << "\n";
}

void flush_buffer(std::ofstream& output_file, std::ostringstream& buffer) {
    output_file << buffer.str();
    buffer.str("");
    buffer.clear();
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input file> <output file>\n";
        return 1;
    }

    std::string input_filename  = argv[1];
    std::string output_filename = argv[2];

    std::ifstream input_file(input_filename);
    if (!input_file.is_open()) return 1;

    std::ofstream output_file(output_filename);
    if (!output_file.is_open()) return 1;

    std::unordered_map<std::string, std::string> object;
    std::string line;

    bool already_parsed_headers = false;
    std::vector<std::string> headers;

    std::ostringstream buffer;
    
    const std::unordered_set<std::string> discard_keys = {
        "beer_name", "user_name", "brewery_name", "style", "abv"
    };

    while (std::getline(input_file, line)) {
        if (line.empty() && !object.empty()) {
            if (!already_parsed_headers) {
                headers.reserve(object.size());
                for (const auto& pair : object) 
                    headers.emplace_back(pair.first);
                write_header(output_file, headers);
                already_parsed_headers = true;
            }
            write_object(buffer, headers, object);
            object.clear();

            if (buffer.tellp() >= BATCH_SIZE) {
                flush_buffer(output_file, buffer);
            }
        } else {
            std::string_view line_view(line);
            auto split_position = line_view.find(":");
            if (split_position != std::string_view::npos) {
                std::string_view key = line_view.substr(0, split_position);
                std::string_view value = line_view.substr(split_position + 2); // +2 to skip ": "

                if (discard_keys.find(std::string(key)) == discard_keys.end())
                    object.emplace(std::string(key), std::string(value));
            }
        }
    }

    if (!object.empty()) write_object(buffer, headers, object);
    flush_buffer(output_file, buffer);

    input_file.close();
    output_file.close();
    return 0;
}
