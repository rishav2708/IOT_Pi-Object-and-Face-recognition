package com.example.rishav.wirelessimage;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Bundle;
import android.provider.MediaStore;
import android.speech.RecognizerIntent;
import android.support.design.widget.FloatingActionButton;
import android.support.design.widget.Snackbar;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.util.Base64;
import android.util.Log;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.graphics.Bitmap;
import android.widget.TextView;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.Socket;
import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    ImageView imageView;
    public static final int PICK_IMAGE_REQUEST=1;
    public static final int SPEECH_REQUEST=100;
    Button imButton;
    ImageButton speak;
    TextView speechOutput;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        //Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        //setSupportActionBar(toolbar);
        imageView=(ImageView)findViewById(R.id.imageView);
        imButton=(Button)findViewById(R.id.pictures);
        speak=(ImageButton)findViewById(R.id.speak);
        speak.setOnClickListener(new View.OnClickListener()
        {

            @Override
            public void onClick(View v) {
                promptSpeech();
            }
        });
        speechOutput=(TextView)findViewById(R.id.textOuput);
        imButton.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View v) {
                Intent intent = new Intent();
                intent.setType("image/*");
                intent.setAction(Intent.ACTION_GET_CONTENT);
// Always show the chooser (if there are multiple options available)
                startActivityForResult(Intent.createChooser(intent, "Select Picture"), PICK_IMAGE_REQUEST);
            }
        });
    }
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == PICK_IMAGE_REQUEST && resultCode == RESULT_OK && data != null && data.getData() != null) {

            Uri uri = data.getData();
            try {
                Bitmap bmap= MediaStore.Images.Media.getBitmap(getContentResolver(), uri);
                imageView.setImageBitmap(bmap);
                InputStream iStream =   getContentResolver().openInputStream(uri);
                byte[] inputData = getBytes(iStream);
                String message=Base64.encodeToString(inputData,Base64.DEFAULT);
                System.out.println(message);
                JSONObject jsonObject=new JSONObject();
                jsonObject.put("type","image");
                jsonObject.put("data",message);
                String json=jsonObject.toString();

                ClientRxThread client=new ClientRxThread("192.168.0.3",5001,json);
                client.start();
            } catch (IOException e) {
                Log.e("Error","Error occured in bitmapping");
            } catch (JSONException e) {
                Log.e("JSON Error","Error while creating one");
            }

        }
        else if(requestCode==SPEECH_REQUEST && resultCode==RESULT_OK && data!=null)
        {
            ArrayList<String> result=data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            String message=result.get(0);
            JSONObject jsonObject=new JSONObject();
            try {
                jsonObject.put("type","speech");
                jsonObject.put("data",message);
                String js=jsonObject.toString();
                ClientRxThread client=new ClientRxThread("192.168.0.3",5001,js);
                client.start();
            } catch (JSONException e) {
                Log.e("JSError","Voila");
            }



            speechOutput.setText(result.get(0));
        }
    }
    private void promptSpeech()
    {
        Intent intent=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT,R.string.speech_prompt);
        try {
            startActivityForResult(intent, SPEECH_REQUEST);
        }catch(ActivityNotFoundException ex)
        {
            Log.d("Debug","Speak Feature not supported");
        }

    }
    public byte[] getBytes(InputStream inputStream) throws IOException {
        ByteArrayOutputStream byteBuffer = new ByteArrayOutputStream();
        int bufferSize = 1024;
        byte[] buffer = new byte[bufferSize];

        int len = 0;
        while ((len = inputStream.read(buffer)) != -1) {
            byteBuffer.write(buffer, 0, len);
        }
        return byteBuffer.toByteArray();
    }
    private class ClientRxThread extends Thread
    {
        String dstAddress;
        int dstPort;
        PrintWriter out;
        String message;
        ClientRxThread(String address, int port,String message) {
            dstAddress = address;
            dstPort = port;
            this.message=message;
        }
        public  String ljust(String word,int count)
        {
            int pad=count-(word.length());
            System.out.println(pad);
            for(int i=0;i<pad-1;i++)
            {
                word+=' ';
            }
            return word;
        }
        @Override
        public void run() {
            Socket socket = null;
            try {
                socket=new Socket(dstAddress,dstPort);
                out=new PrintWriter(socket.getOutputStream());
                int l=message.length();
                String l1=Integer.toString(l);
                out.println(ljust(l1,16));
                out.flush();
                out.println(message);
                out.flush();
                socket.close();
            } catch (IOException e) {
                e.printStackTrace();
            }

        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }
}
