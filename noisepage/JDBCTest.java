import java.sql.*;

public class JDBCTest {

  private static final String DB_URL =
   "jdbc:postgresql://localhost:15721/terrier?preferQueryMode=extended";
  private static final String DB_USER = "terrier";
  private static final String DB_PASS = "";

  private static final String[] SQL_STRINGS = new String[]{
    "CREATE TABLE foo (a int)",
    "CREATE INDEX bar ON foo (a)"
  };

  public static void main(String[] args) {
    Connection conn = null;
    Statement stmt = null;

    try {
      Class.forName("org.postgresql.Driver");
      conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
      stmt = conn.createStatement();
      for (String sql : SQL_STRINGS) {
        stmt.execute(sql);
      }
      stmt.close();
      conn.close();
    } catch (Exception e) {
      e.printStackTrace();
    }
  }

};
